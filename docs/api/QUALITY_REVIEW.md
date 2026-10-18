# 认证质量审阅与任务反馈：实际接口与消费

2026-10-18，A17，开发环境认证入口已部署。完整策略、对象和代码目录见 [A17](../implementation/MS-I2m-A17.md)；源码权威为 `src/uaw/shared/quality.py`、`contracts/quality_catalog.py` 及生成的 `contracts/uaw.schema.json`、OpenAPI。原 C 评分器与 A11 导入契约保持。

## 模块链路

可信操作员 `ops/quality_review.py register` → 只读重建实际 Run 与固定四文件 → `QualityReviews` 为指定所有人登记空白包 → 原浏览器会话认证/Origin/CSRF → `HttpQualityPort` → 草稿 CAS / 本人显式提交 → A11 导入 → 原 C 四文件导出。单独的 `save_feedback` 只保存原 Run/input 版本的意见。

跨库采集须由操作员显式提供受保护 `--source-settings`；源库只读，目标仅登记审阅，不复制诊断 Run。网页没有任意路径、源库、用户或模型配置参数。操作命令不在输出中回显凭据。

## HTTP

沿用 0.1 `{meta, payload}` 写请求与原 ok/failure 响应。`meta.expected_revision` 为草稿/反馈修订，创建反馈为 0；request_id 重放仅返回相同原请求的回执，不能改参数。身份由会话解析，不接收自报 reviewer。

| 入口 | 输入 | 输出 | 约束 |
| --- | --- | --- | --- |
| `GET /v1/quality/reviews` | 可选 cursor | `QualityReviewPage` | 所有人隔离、每页至多 25 |
| `GET /v1/quality/reviews/{id}` | 原审阅 ID | `QualityReviewView` | 完整固定目标和最新草稿/冻结提交 |
| `POST /v1/quality/reviews/{id}/draft` | packet_sha256、全部 judgments | `QualityReviewView` | 未知可保存；严格目标清单、摘要、CAS |
| `POST /v1/quality/reviews/{id}/submission` | 同上及 human_attested=true | `QualityReviewView` | 证据已核对、必需判断及意见完整；质量可接受需明确无关键错误及虚构证据；成功后冻结 |
| `GET /v1/quality/reviews/{id}/export` | 原审阅 ID | `QualityExport` | 仅已提交；原四文件字符串、审阅与提交摘要、认证人、basis |
| `GET /v1/runs/{id}/feedback` | 本人原 Run ID | `QualityFeedbackPage` | 原任务所有权；与事实评分分开 |
| `POST /v1/runs/{id}/feedback` | feedback_id、run_revision、input_revision、category、notes | `QualityFeedback` | 独立 CAS，固定原历史版本，不能改绑任务 |

## 对象与版本

- `QualityOrigin` 标明实际或受控来源、来源用户、Run/input/源码版本。目标审阅用户另由可信登记指定。
- `QualityTarget` 包含原 Case/Answer、固定绑定和原模型核验；`verification_outputs` 保留 Reviewer 原文、调用 ID 与输出摘要。没有核验的普通回答不伪造核验。
- `QualityJudgment` 除 case_id/attempt_id 与 notes 外，题目标准、证据阅读、事实正确、要求保留、阻断、虚构执行、关键错误、虚构证据及可接受判断初始均为 null。unknown 不转换成 false。
- `QualityReviewView` 的 revision 独立于 Run；packet_sha256 固定原材料与回答。服务保存审阅版本和审计，拒绝旧包、漏项、重复目标或错配回答。
- `QualityExport.files` 为 suite、manifest、observations、reviews 四个原格式文件字符串；原 observations 不改写。`controlled_test` 无法导出为真正人审依据。导出供原 C 评测器使用，不能仅凭成功下载宣称质量通过。
- `QualityFeedback` 的 id/revision 与 Run 分离，保存创建/更新时间、原 Run/input 版本、类别和意见。更新仍指向原版本；不操作 job、clock、budget、Item 或成果接受。

页面遇到网络结果不确定或 CAS 冲突，禁用继续写入，先由本人读取保存结果；不自动重发。原对象拒绝后不留部分提交。退出/切换身份时中止旧读取并卸载表单，不能把旧用户迟到响应显示给新身份。

[逐字段字典](OBJECTS.md) · [生成 HTTP](HTTP.md) · [测试操作](../implementation/human-tests/H02-v9.md) · [实际验证索引](../implementation/evidence/ms-i2m-a17-completion-audit.json)
