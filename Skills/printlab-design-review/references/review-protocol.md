# 外观内审与用户确认协议

## 评分含义

“90%”在此落实为 **100 分制的证据支持型视觉内审至少 90 分**。它不是像素相等率，不是模型识别置信度，也不是物理、工程或安全合格率。程序核算分数、来源和失效条件；视觉判断仍需要实际查看设计稿与模型。不得把 SSIM、CLIP 或一张漂亮渲染的数值直接称作造型还原率。

| 项目 / 记录键 | 权重 | 需要比较 |
|---|---:|---|
| 轮廓 silhouette | 30% | 外轮廓、宽身/高身、顶部/侧边/底部走向 |
| 比例 proportions | 20% | 宽高深关系，部件大小和占主体的比例 |
| 曲面 surfaces | 20% | 鼓起/凹陷、圆润程度、过渡与侧面厚度 |
| 特征位置 feature_layout | 20% | 眼鼻口、耳脚、格栅等位置/间距/方向 |
| 细节 details | 10% | 边缘、孔格、脚趾等可见特征，不用配色和光照掩盖几何差别 |

总分 = 各项分数 × 固定权重之和。每项 0–100，必须写观察和扣分理由，附文件路径与 SHA。不做先四舍五入再过门槛。缺项、未知分数、证据失效都算未通过，不按 0 或 100 自动补齐。总分未达 90 时继续内部返工。

评分锚点：100 为可见目标特征没有发现差异；90 为关键轮廓与比例吻合、仅剩局部轻微差异；80 为方向相近但仍可明显看出某处比例或曲面差异；更低表示存在显著偏差。不得对未看见的面给 100。评价同一设计时保持相同标尺，不通过改评分定义“提高相似度”。

每项观察尽可能包含同视角下的归一化比例、轮廓叠加、特征位置或局部放大对比；数值的测量方法和不确定性注明。图片像素不能直接当实物毫米尺寸。单张图不可观测的背面列为设计假设，关键视图冲突未解决前不通过。

**一票阻断项**：选错主稿、整体形态不对、缺失关键特征、非等比拉伸伪装比例、来源不一致或重大差异未解决。各目标特征均须有通过证据，高分不能抵消这些问题。

## 记录位置

- `Review/design-target.json`：保留真实选图与哈希、关键特征、所选三视图、未解决冲突。目标变化使旧评审失效。
- `Review/design-gates/vNNN.json`：从 `Templates/Project/Review/design-gate.json` 创建该版本记录；不覆盖旧版本。
- `Review/appearance-approvals/vNNN.json`：从 `Templates/Project/Review/appearance-approval.json` 建立真实用户决定。未得到确认时保持 pending，不伪填 quote/source。

评分记录包含原有 `target_contract_sha256`、`primary_sha256`、`model`、`reviewer`、`findings`、逐目标 `features` 与模型 `renders`，另加：

- `source_files`：本版可编辑建模源和实际使用参数，各条 `{path, sha256}`，位于 `Design/vNNN/`。
- `model`：本版完整外观装配的 `{path, sha256}`，位于 `Exports/vNNN/`，支持 STL 或 STEP；不能拿单个元件参考体替代整个模型。
- `renders`：所需每个视图的 `{path, sha256, model_sha256}`。实际渲染还应保留源网格的来源链，不能只手填绑定关系。
- `similarity.method`：`rubric-v1`。
- `similarity.criteria`：恰好上述五个键；每项含 `score`、`observations`、`deductions`、`evidence`。evidence 为非空 `{path, sha256}` 文件记录列表；即使不扣分也说明未发现何种偏差。
- `similarity.comparison`：实际并排对照图 `{path, sha256}`。
- `similarity.view_alignment`：`status=matched`、`scale=uniform`、`nonrigid_warp=false`、`notes` 描述实际相机/投影匹配方式和局限。
- `similarity.blocking_differences`：重大差异列表。必须明确为空才具备交稿资格，不能仅遗漏此字段。

命令：`./Harness/bin/printlab design-check P001 --stage appearance --revision vNNN`。P001 只是示例，应使用实际项目 ID。程序通过后才进入用户外观审稿。

用户确认记录应包含 `status=confirmed`、`actor=user`、真实 `quote/source`、`revision`、`model_sha256`、`target_contract_sha256`、`review_sha256`（准确评分记录文件的 SHA）。概念选图、内部 Reviewer 的 accepted、用户要求配置工作流、沉默或“先继续做”不能自动当本轮真实模型验收。用户明确要求修改时保存 `status=needs_changes` 和实际原话，进入新版本。

命令：`./Harness/bin/printlab design-check P001 --stage release --revision vNNN`。模型、源文件、参数、原稿、渲染或评分记录改变，须重新核对，旧确认不得自动继承。界面显示的阶段从有效证据推导，单改 project.status 为 awaiting_review 不能越过评分门槛。

本检查既不会测量真实装配，也不会获得打印许可；后续仍执行工程、切片与具体打印检查。
