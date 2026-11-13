"""Offline workflow regressions; synthetic ratings are not production assessments."""
import math
import pytest
from fastapi.testclient import TestClient
from printlab import core, design, appearance, cli, project3mf
from printlab.api import app
from test_design_target import locked, make_release


def save(p, review):
    core.write_json(p / 'Review/design-gates/v003.json', review)


def test_score_90_opens_review_but_cannot_replace_user_approval(locked):
    p, _, r = make_release(locked)
    (p / 'Review/appearance-approvals/v003.json').unlink()
    result = design.check('P001', 'appearance', 'v003')
    assert result['status'] == 'passed' and result['similarity_score'] == 90
    assert design.check('P001', 'release', 'v003')['status'] == 'blocked'
    with pytest.raises(core.WorkflowError, match='User has not confirmed'):
        project3mf.export('P001', 'v003', 'none', 'none', ['none'], 'Textured PEI Plate')
    assert appearance.workflow('P001', 'v003')['phase'] == 'awaiting_user_review'


@pytest.mark.parametrize('value', [89.999, 0, None, True, float('nan'), float('inf'), 101, -1])
def test_low_missing_and_invalid_scores_cannot_pass(locked, value):
    p, _, r = make_release(locked)
    for row in r['similarity']['criteria'].values():row['score'] = value
    save(p, r)
    assert design.check('P001', 'appearance', 'v003')['status'] == 'blocked'


@pytest.mark.parametrize('change', ['missing_criterion', 'missing_evidence', 'changed_evidence', 'source_changed', 'warp', 'major_difference', 'feature_failed'])
def test_high_scores_cannot_cover_missing_or_contradictory_evidence(locked, change):
    p, _, r = make_release(locked)
    for row in r['similarity']['criteria'].values():row['score'] = 100
    s=r['similarity']
    if change=='missing_criterion':del s['criteria']['surfaces']
    elif change=='missing_evidence':s['criteria']['surfaces']['evidence']=[]
    elif change=='changed_evidence':(p/s['comparison']['path']).write_bytes(b'changed')
    elif change=='source_changed':(p/r['source_files'][0]['path']).write_bytes(b'changed source')
    elif change=='warp':s['view_alignment']['nonrigid_warp']=True
    elif change=='major_difference':s['blocking_differences']=['wrong silhouette']
    else:r['features']['silhouette']['result']='fail'
    save(p,r)
    assert design.check('P001','appearance','v003')['status']=='blocked'


def test_changed_review_invalidates_old_user_confirmation(locked):
    p, _, r = make_release(locked)
    assert appearance.workflow('P001','v003')['phase']=='appearance_confirmed'
    r['similarity']['criteria']['details']['deductions']='different finding'
    save(p,r)
    assert appearance.workflow('P001','v003')['phase']=='awaiting_user_review'
    assert design.check('P001','release','v003')['status']=='blocked'


def test_user_rejection_returns_to_internal_work(locked):
    p, _, r=make_release(locked)
    path=p/'Review/appearance-approvals/v003.json';a=core.read_json(path);a['status']='needs_changes';core.write_json(path,a)
    assert design.check('P001','appearance','v003')['status']=='blocked'
    assert appearance.workflow('P001','v003')['phase']=='internal_revision'
    assert not appearance.workflow('P001','v003')['eligible_for_user_review']


def test_api_does_not_show_stale_awaiting_review_before_gate(locked):
    p, _, r=make_release(locked)
    data=core.read_json(p/'project.json');data.update(current_revision='v003',status='awaiting_review');core.write_json(p/'project.json',data)
    r['similarity']['criteria']['silhouette']['score']=50;save(p,r)
    client=TestClient(app)
    for row in [client.get('/api/projects').json()['projects'][0],client.get('/api/projects/P001').json()]:
        assert row['status']=='appearance_revision'
        assert row['appearance_workflow']['phase']=='internal_revision'
        assert row['appearance_workflow']['score']==78
        assert row['appearance_workflow']['print_authorized'] is False
    assert cli.main(['design-check','P001','--stage','appearance','--revision','v003'])==2


def test_custom_assembly_export_is_supported_without_reference_substitution(locked):
    p, _, r=make_release(locked)
    old=p/r['model']['path'];new=old.with_name('assembly-appearance.stl');old.rename(new)
    r['model']['path']=str(new.relative_to(p));save(p,r)
    assert design.check('P001','appearance','v003')['status']=='passed'
    r['model']['path']='Exports/v003/component-REFERENCE.stl';new.rename(p/r['model']['path']);save(p,r)
    assert design.check('P001','appearance','v003')['status']=='blocked'
