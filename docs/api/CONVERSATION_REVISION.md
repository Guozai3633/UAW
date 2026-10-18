# 2026-10-18：成果审阅等待计时补齐

A16 在真实成果 Item/完整交付/idle 来源证明下，将审阅等待登记为原时钟 waiting_for_user，并原子停放后台 job；接受直接收尾，纠正按剩余额度续跑。原问题等待、HTTP/clock 对象结构及授权期限保持。精确内部接口、输入输出、拒绝条件和装配见 [A16 审阅等待契约](../coordination/requests/A/H02-I04-A16-review-wait-contract.md)，实际验证/部署见 [H02-I04](../implementation/human-tests/H02-I04.md)。下方“尚未注入”等内容为历史阶段，不代表最新 H02 服务状态；本机/Tool 完整门槛仍独立。

# 2026-10-16：MS-I2m A6 内部执行段

新增 `InternalRunActiveSegment` 作为服务端持久记录；五个控制 HTTP、0.2 meta 和原 1403 个 schema 保持。显式注入 A 执行段组件及实际 D clock 的候选实例，可为尚未发出的新调用按剩余主动额度派生新上下文；预算、权限、Context、消息及文本成果共同复查其来源。旧 Run 预算、账本、调用、预留、审批和本机授权的原期限均保留。具体字段见 [内部执行段](objects/InternalRunActiveSegment.md)，算法/目录/边界见 [A6 实施](../implementation/MS-I2m-A6.md)。

默认尚未注入新段或真实 D clock；Tool dispatch 跨原墙钟的 port 仍未接线，因此本段不能作为完整 M2、真实长等待、Tool、H02 或新测试服务已通过的声明。当前准确阶段以 [DISPATCH](../coordination/DISPATCH.md) 为准。下方 A5 和更早阶段继续作为历史保留。

# 2026-10-16：MS-I2m A5 的实际可用范围

五个控制 HTTP 已实现原账号读图、回答/纠正持久受理、幂等回执及 Origin/CSRF 检查。正式恢复组装在新候选实例中显式注入 `ConversationClockPort` 后启用：HTTP 只通知，原队列空闲时从数据库扫描并恢复原 Run；实际模型消费后才提交 applied。具体实现、目录与回执见 [A5 实施记录](../implementation/MS-I2m-A5.md)，准确阶段 SHA 以 [DISPATCH](../coordination/DISPATCH.md) 为准。

受理、后台唤醒、实际生效、完成及用户接受是不同状态。响应丢失或进程重启可找回已受理的原输入；无法恢复时保留原 Failure 和稳定 Item，不让用户重新提交同一补充。未知调用先对账；原执行期限仍有效。

**默认尚未安装 D 的生产计时组件，当前 H01-v5 服务未替换；长时间等待后的可信新执行段和实际 H02 联调仍待完成。** 下面较早记录的“仅契约/handler 未安装”描述的是各历史阶段，当前状态以本节和正式派发记录为准。

# 2026-10-16：MS-I2m新增精确问题发现读图

P1-13单次普通回复已实跑，H01-v5普通问答本人反馈认可。原Run续跑/计时仍待实际接线。本轮新增GET /v1/runs/{run_id}/conversation与RunConversationView，精确字段/允许目录/来源见[固定接口](../coordination/requests/A/MS-I2m-AD-contract.md)及[正式分包](../coordination/requests/A/MS-I2m-parallel-packages.md)。五个控制HTTP当前均仅契约，未安装handler，不能当已可调用。

0.2兼容扩展不改变旧1399个命名schema；新增读图及其结果/请求封装共3个结构，原0.1与P1-12控制DTO保持。以下为原设计，当前可用性以DISPATCH及阶段实现为准。

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
