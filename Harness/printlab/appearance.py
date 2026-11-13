"""Evidence-backed visual review, separate from user acceptance and print permission."""
from __future__ import annotations

import math
import re
from pathlib import Path
from . import core

MINIMUM = 90
RUBRIC = {"silhouette": ("轮廓", 30), "proportions": ("比例", 20),
          "surfaces": ("曲面", 20), "feature_layout": ("特征位置", 20),
          "details": ("细节", 10)}


def assess(pp, revision, review, asset, issues):
    """Validate recorded observations and compute their score; never infer pixels."""
    s = review.get("similarity") or {}
    rows = s.get("criteria") or {}
    valid_scores = isinstance(rows, dict) and set(rows) == set(RUBRIC)
    if s.get("method") != "rubric-v1" or not valid_scores:
        issues.append("Similarity requires the complete rubric-v1 assessment")
    total = 0.0
    for key, (_, weight) in RUBRIC.items():
        row = rows.get(key, {}) if isinstance(rows, dict) else {}
        score = row.get("score") if isinstance(row, dict) else None
        valid = type(score) in (int, float) and math.isfinite(score) and 0 <= score <= 100
        valid_scores = valid_scores and valid
        if not valid:
            issues.append(f"Similarity score is missing or invalid: {key}")
        else:
            total += score * weight / 100
        if not isinstance(row, dict) or not row.get("observations") or not row.get("deductions"):
            issues.append(f"Similarity observations and deduction reasons required: {key}")
        evidence = row.get("evidence", []) if isinstance(row, dict) else []
        if not isinstance(evidence, list) or not evidence:
            issues.append(f"Similarity comparison evidence required: {key}")
        else:
            for record in evidence:
                asset(record, f"similarity.{key}.evidence")
    score = total if valid_scores else None
    # Do not round 89.999 up to the 90-point submission boundary.
    if score is None or score < MINIMUM:
        issues.append("Visual similarity must reach at least 90/100 before user review")
    alignment = s.get("view_alignment") or {}
    if (alignment.get("status") != "matched" or alignment.get("scale") != "uniform"
            or not alignment.get("notes") or alignment.get("nonrigid_warp") is not False):
        issues.append("Comparison requires matched views, uniform scale and no non-rigid warping")
    if not isinstance(s.get("blocking_differences"), list) or s["blocking_differences"]:
        issues.append("Unresolved major appearance differences block submission regardless of score")
    asset(s.get("comparison"), "similarity.comparison")
    sources = review.get("source_files", [])
    if not isinstance(sources, list) or not sources:
        issues.append("Appearance review must bind editable model sources and parameters")
    else:
        for source in sources:
            f = asset(source, "appearance_source")
            if f and not f.is_relative_to(pp / "Design" / revision):
                issues.append("Appearance source must belong to the reviewed revision")
    decision_path = pp / f"Review/appearance-approvals/{revision}.json"
    if decision_path.exists():
        decision = core.read_json(core.safe_path(pp, str(decision_path.relative_to(pp))), {})
        if decision.get("status") == "needs_changes":
            issues.append("User requested changes; create and review a new revision")
    return score


def approval_issues(pp, revision, review, contract_hash):
    """Only a user decision on this exact evidence bundle releases appearance."""
    path = pp / f"Review/appearance-approvals/{revision}.json"
    try:
        d = core.read_json(core.safe_path(pp, str(path.relative_to(pp))), {})
    except (ValueError, OSError):
        d = {}
    gate_path = core.safe_path(pp, f"Review/design-gates/{revision}.json")
    valid = (d.get("status") == "confirmed" and d.get("actor") == "user"
             and bool(d.get("quote")) and bool(d.get("source"))
             and d.get("revision") == revision
             and d.get("model_sha256") == review.get("model", {}).get("sha256")
             and d.get("target_contract_sha256") == contract_hash
             and d.get("review_sha256") == core.digest(gate_path))
    return [] if valid else ["User has not confirmed this exact appearance revision and review bundle"]


def workflow(pid, revision=None):
    from . import design
    pp = core.project_path(pid)
    revision = revision or core.read_json(pp / "project.json", {}).get("current_revision")
    base = {"revision": revision, "threshold": MINIMUM, "score": None,
            "score_basis": "evidence_backed_visual_rubric_not_pixel_similarity",
            "eligible_for_user_review": False, "user_confirmed": False,
            "print_authorized": False}
    if not (pp / design.CONTRACT).exists():
        return {**base, "phase": "not_configured"}
    if not revision or not re.fullmatch(r"v\d{3,}", revision):
        return {**base, "phase": "internal_revision", "issues": ["No model revision to review"]}
    try:
        result = design.check(pid, "appearance", revision)
        base["score"] = result.get("similarity_score")
        if result["status"] != "passed":
            return {**base, "phase": "internal_revision", "issues": result["issues"]}
        base["eligible_for_user_review"] = True
        release = design.check(pid, "release", revision)
        base["user_confirmed"] = release["status"] == "passed"
        # An explicit rejection starts another adjustment round even if the old score was high.
        decision = core.read_json(pp / f"Review/appearance-approvals/{revision}.json", {})
        if decision.get("status") == "needs_changes":
            return {**base, "eligible_for_user_review": False, "phase": "internal_revision",
                    "issues": ["User requested changes; create and review a new revision"]}
        return {**base, "phase": "appearance_confirmed" if base["user_confirmed"] else "awaiting_user_review",
                "issues": release["issues"]}
    except (OSError, ValueError, TypeError, AttributeError, KeyError):
        return {**base, "phase": "internal_revision", "issues": ["Appearance evidence is unreadable or incomplete"]}
