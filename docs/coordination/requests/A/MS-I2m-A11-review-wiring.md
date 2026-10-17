# A11审阅包与导入接口

2026-10-17；A自有来源适配。准确源码见DISPATCH的`ms-i2m-a11-source`，不派发新的B/C/D包。C字段保持冻结，不新增用户HTTP或模型Tool。

## 1. 准备与文件

```text
python ops/conversation_review.py prepare --source <原四文件目录> --output <新的目录>
```

原目录必含Suite/Manifest/Observations/Reviews；使用C原Reader，后续固定所选实际完整回答，拒绝原文件变化、错误摘要/库存/原材料及既有人审/基线。

输出`packet.json`和`index.html`。页面离线，不上传、发起模型调用、自动勾选或保存人审。表单下载文件由本人提供，A不能替本人选择判断。

### ReviewPacket `uaw.human-review-packet.v1`

| 字段 | 类型与约束 |
| --- | --- |
| schema_version | 固定版本字符串 |
| created_at | UTC，准备时刻不早于最后模型回答 |
| input_sha256 | C NamedHash数组：suite/manifest/observations/reviews原字节摘要；导入逐项一致 |
| targets | 1–128个ReviewTarget；逐个对应源候选selection，不扩展路径或URL |
| ReviewTarget.case_id/case_version/case_sha256 | 原Case ID、版本及完整规范JSON摘要 |
| ReviewTarget.manifest_id/attempt_id/output_sha256 | 原候选及实际完整Answer ID/摘要，包含decision/text/evidence，不只正文 |

## 2. 本人提交格式

### ReviewSubmission `uaw.human-review-submission.v1`

| 字段 | 类型与约束 |
| --- | --- |
| schema_version/packet_sha256 | 固定版本/完整packet规范摘要 |
| reviewer_id | C Identifier，1–128字符；操作者自报，不证明账号认证 |
| reviewed_at | UTC，不能早于包准备或晚于当前时钟5分钟以上 |
| human_attested | 必须真正bool true，数字1、false或字符串不接受 |
| items | 1–128个SubmittedReview；与原目标集合完全一致、不重复 |
| item.case_id/attempt_id | 当前包原目标，不允许指定其他回答 |
| item.case_review | verified或needs_revision；后者保留/恢复题目待审 |
| item.evidence_reviewed | 必须真正bool true，表示操作者声明核对实际列出的材料 |
| item.labels | C Labels；正确性/阻断/无证据执行/保留要求/可用可为bool或null；critical_error必须bool |
| item.notes | 1–16384字符的实际核对说明，纯空白拒绝 |

Labels的`acceptable=true`要求`answer_correct=true`、`requirements_preserved=true`、`unnecessary_block=false`、`unsupported_execution=false`且`critical_error=false`。其余未知不自动填为正确或错误。

## 3. 导入

```text
python ops/conversation_review.py import --source <原四文件目录>
  --packet <packet.json> --submission <本人下载的记录.json>
  --basis human_evidence_review --ack-human-input --output <新目录>
```

`--ack-human-input`表示操作者确认持有真正人工判断；不是密码学证明或模型可以代做的判断。构造测试只用`--basis controlled_test`，不会新增人工核准。参数解析支持两种basis，不接纳任意类型。

先完整校验来源和提交再新建输出；失败返回2，stdout只有`review_operation_rejected`、安全code与异常类型，不回显私有文字/凭据/路径。成功0，输出数量/basis/0新增调用/0运行写入。目录存在直接拒绝，部分IO失败保留现场，不覆盖或自动重试。

新目录含四文件、原packet/submission及`review-import.json`。Observations原字节保留；Suite只更新合法人审元数据，Manifest只更新Suite摘要；原政策、模型、库存和成本保持。审计明确`human_identity_authenticated=false`，记录原四输入/packet/submission摘要、basis及未裁决发布。

使用原`ops/evaluate_conversation.py`重新读取新四文件后才产生评分报告。本轮仅在构造数据验证导入，真实任务没有人审文件，实际门槛仍待完成。事后导入不改变事前登记状态，Reviewer passed不会生成Review。

HTML脚本仅由固定源码摘要获准执行，所有任务和材料内容均用textContent；CSP禁止网络、外部资源、base和form提交，下载仅本机Blob。实际浏览器被file协议策略拒绝，本轮显示/下载保留pending，不以静态检查替代。

[策略与目录细分](../../../implementation/MS-I2m-A11.md) · [机器回执](../../../implementation/evidence/ms-i2m-a11.json)。
