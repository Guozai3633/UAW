# 对话快通路与原任务续跑：接口修订设计

2026-10-14，架构v0.11。**P1-12已加入契约目录0.2/schema/OpenAPI及Python严格消费者；新HTTP与运行流程仍未装配，不能当已可调用接口。** 原0.1对象/动作/期限保持，新对话控制meta为0.2。精确消费与可用性见 [P1-12固定协议](../coordination/requests/A/H02-P1-12-ports.md) 和 [本轮回执](../implementation/P1-12.md)。依据：[ADR-001](../decisions/ADR-001-conversation-and-delivery.md)、[详细执行设计](../design/CONVERSATION_EXECUTION.md)。

## 1. 先固定什么，再开发什么

A已发布精确字段与URL，准确源码在DISPATCH页首。新handler/事务/迁移/事件尚未安装，旧Run不自动转换；B/C/D仍需正式新包才开工，不据schema存在宣称实际来源已准备。已有Tool/Runner准入不变。

## 2. 对象与输入输出

下表说明信息归属；精确请求/结果以生成对象为准。ContinueRun对应RunClarificationAnswerRequest/RunContinuationReceipt，CorrectRun对应RunCorrectionRequest/RunContinuationReceipt，ExecutionClock对应RunExecutionClock。补充对象另有ConversationProtocolBinding、ClarificationProposal/Question/View、RunInputPatch；后续EvaluationCase/Report仍由P1-15独立建设。

| 对象/入口 | 输入 | 输出 | 约束 |
| --- | --- | --- | --- |
| FirstDecision（Agent） | 原 InputRef、有效补充、最小 Context、固定模型/可见能力、预算 | reply / tool / ask / deliver 的类型分支；可选理解摘要及实际模型来源 | 必须有唯一可辨动作；控制权限由 Runtime 注入；直接 reply 不要求先有独立理解调用 |
| ReplyProposal（Agent→Run） | 原模型结果引用、消息内容/来源、预期输入与 Run 版本 | 稳定 message Item、合法终态回执 | 当前来源/取消/费用/依赖效果复核；不要求 Artifact 或 VerificationReport，不自动接受成果 |
| ClarificationQuestion（Agent→Run） | 问题文本、原因、所需内容、关联输入版本、可选候选 | 稳定 question Item、waiting 原因、暂停检查点 | 具体问题可见；原始模型来源可追溯；重启去重；不能把提问当权限批准 |
| ContinueRun（UI→Ingress→Run） | run_id、question_item_id、expected_run_revision、expected_question_revision、request_id、回答文本/已授权材料引用 | operation/input 引用、接受的修订、当前状态/事件 cursor | 主体/会话归属、CAS、幂等；已取消/已终态拒绝；不是创建新 Run |
| CorrectRun（UI→Ingress→Run） | run_id、预期版本、幂等键、纠正文本/引用、适用范围 | 追加 InputRecord、控制接受回执、实际生效边界 | 受理与实际生效分开；只失效受影响结果；已发生效果不能自动撤销 |
| ExecutionClock（Run 内部） | 累计主动耗时、当前段开始、pause 原因/开始、预算/策略版本 | 剩余主动时间、等待耗时、恢复检查点 | 持久化及租约保护；恢复不重领全额；已派发调用 deadline 与授权期限不变 |
| EvaluationCase/Report（Support） | 样本版本、人工事实依据/反例、候选/基线源码+提示词+模型配置、全部 attempt | 答案错误/漏判/阻断指标、调用/等待/费用与结论 | 无 Reviewer 记 N/A；完整失败/pending 不删；不写用户接受 |

复用现有InputRecord、InteractionItem、Run/Usage，新输入关系单独由RunInputPatch表达，原对象不新增必填字段。契约唯一入口为contracts/interface_catalog.py，conversation_catalog.py被finalize注册；不使用不存在的schema_catalog.py，不维护第二份JSON schema。

## 3. 等待与续跑状态约束

```text
running → 持久问题 + waiting_for_user + clock暂停
waiting_for_user → CAS追加回答 → 当前授权/费用/取消复核 → preparing/running
running → 纠正受理 → 到安全边界更新输入/上下文 → running 或具体受阻
任意非终态 → cancelled（随后答复不能复活）
completed/failed/cancelled → 新要求创建新Run
```

具体状态按现有允许转换扩展，不能仅更新前端字串。问题 Item、Run 等待和时钟暂停同域事务提交，Outbox 顺序可恢复；跨域只使用版本化引用/操作回执，不承诺巨型原子事务。

续跑回答不是恢复旧 invocation：旧调用只能查询原回执/对账；新合法调用领取剩余主动执行段期限。审批、配对、root/file 当前权限独立复查，原参数/版本变化按原规则拒绝。

## 4. 失败及兼容迁移

| 情况 | 应有行为 |
| --- | --- |
| 响应丢失，同键重试 | 返回既有受理及当前状态，不创建输入/Run/模型第二次调用 |
| 两个页面答复同一问题 | CAS 一个成功，另一个读当前版本；相同幂等请求复用 |
| 旧问题、取消、已终态、过期资料 | 明确 conflict/stale/denied，返回可读恢复指引，不静默当新任务 |
| 续跑预算不足、授权失效、效果 unknown | 明确停点；授权不自动延长，unknown 对账不重发 |
| 数据库提交失败、进程崩溃 | 原输入/状态不半提交；恢复租约后查询原操作，时钟不重复计算 |
| 旧客户端不支持新问答 | 保留问题可见、历史可读；不谎称已续跑；升级提示明确 |
| 旧 Run/成果记录 | 保留原交付/接受/费用语义；不批量改成快速聊天，不复活取消任务 |

旧 Run 缺执行段信息不能推算为免费等待；按其固定原预算语义结束或明确新建 Run。新模式应记录协议/策略版本，读旧数据兼容，旧服务遇到新控制动作拒绝而不是误执行。

## 5. 接口验收

接口轮必须验证实际消息-only完成、一次首次调用来源消费、同 Run 问答、纠正生效边界、幂等/CAS、取消竞态、重启/刷新、等待超原执行时限后的合法续跑及过期授权拒绝。正式成果继续验证真实引用/版本/接受条件。完整本机文件验收不混入文本接口轮的完成声明。
