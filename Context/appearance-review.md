# 外观迭代与审稿

外形选图 → 真实外观模型 → 同源对照评分 ↔ 调整 → 内审至少90/100 → 用户审稿 ↔ 修改 → 用户明确确认 → 正式结构设计。

完整可调用技能位于 [Skills/printlab-design-review](../Skills/printlab-design-review/SKILL.md)，评分标准、证据格式和确认规则的维护入口是[评分与记录协议](../Skills/printlab-design-review/references/review-protocol.md)。可将整个技能目录安装到本机 Codex skills 目录。

`design-check --stage appearance` 检查交稿资格；`--stage release` 额外要求真实用户对该版本和证据的确认。90分为有证据的视觉内审，不宣称客观像素还原率。几何检查、内部接受或项目状态字段不能代替这两道检查。

新版本创建后默认仍是内部调整；用户要求修改继续迭代，不能把待修改稿重新标成合格稿。内部空间占位可提前检查，正式安装结构与制作在外观确认后推进；结构若影响外形，重回循环。所有阶段均不自动授予打印权限。
