# MS-I2m：开工接口与来源约定

2026-10-16，A 维护。共同基线标签 `ms-i2m-start`；准确40位SHA见远端DISPATCH页首正式发布记录。标签不移动，后续阶段接口另发准确SHA。本文件固定可独立开发的边界，不代表新HTTP或暂停续跑已上线。

## 1. 已有来源与兼容

- P1-13 source `305bd0a3ff7896f000a0f2dd5210d710f385a09f`，实际普通聊天一次固定模型调用、消息完成已验证。用户本次“可以了”只记录H01-v5普通问答复体验认可，不扩大为H02/专业事实/本机整链接受。
- 对话协议 `conversation-v1`，新控制meta `0.2`；旧0.1 DTO、Run、总费用、原调用和授权期限不变。已有新Run会持久化协议/clock，旧Run不批量转换。
- 唯一公共字段源 [conversation_catalog.py](../../../../contracts/conversation_catalog.py)，Python [conversation.py](../../../../src/uaw/shared/conversation.py)。没有权限、主体、模型切换字段可由页面或模型自报。
- 本轮B页面与D计时使用这些已提交类型；C评测用隔离输入文件，不接管理员HTTP。缺生产依赖不能回填mock成功。

## 2. A→B：HTTP、发现问题与回执

| 方法 | 路径 | 结果/用途 |
| --- | --- | --- |
| GET | `/v1/runs/{run_id}/conversation` | 新增 `RunConversationView`，当前Run/输入版本、开放问题、既有补充request_id；问题ID来自持久记录 |
| GET | `/v1/runs/{run_id}/clarifications/{question_item_id}` | `ClarificationView`，指定问题原版本；旧问题也可读 |
| POST | `/v1/runs/{run_id}/clarifications/{question_item_id}/answers` | `RunContinuationReceipt`，回答原问题 |
| POST | `/v1/runs/{run_id}/corrections` | `RunContinuationReceipt`，原非终态Run补充纠正 |
| GET | `/v1/runs/{run_id}/continuations/{request_id}` | 原提交最新accepted/applied/superseded/cancelled回执 |

`RunConversationView = {protocol, run:RunRecord, input_revision, continuation_request_ids:ID[0..64], question?:ClarificationView}`；没有开放问题时省略question，不发送null。question与当前run.id/conversation_id/revision/status/input_revision匹配，只在open+waiting时返回。工具审批/成果接受仍走原端点，不能因为Run.waiting就猜成澄清。列表按补充输入版本排序，有界64，与原输入集限制一起校验。

写入沿用P1-12 `{meta:{request_id,schema_version:"0.2",expected_revision},payload:{expected_input_revision,text,attachment_refs,...}}`；回答另含expected_question_revision，路径ID不在payload重复。读取用 `X-UAW-Schema-Version: 0.2`。沿用真实cookie、精确Origin、CSRF和CLI认证；**现有通用body只接受0.1，A负责分支解析，不把新meta交给旧RequestMeta强转**。

`accepted`仅表示不可变原Input/patch已保存；`applied`必须有安全边界和实际消费版本证据。响应丢失先查同一request_id；同键同参数复用原受理并返回最新状态，同键异参409。当前Run CAS冲突409、输入/问题失效412、终态/取消409、归属403、认证401、旧协议/缺实际来源503。错误沿用已有Failure封装。刷新不自动重发，不生成新Run，不自动停止或接受。

稳定消息Item仍为InteractionItem。`item.updated`/`run.updated`已有事件通知后重读上述读图，事件payload不临时加未登记字段。受理/生效由回执patch.state表达。B可立即用此精确合同开发受控服务；实际端口在A阶段回执公布前记pending，不能用H01-v5旧端口404当新功能联调失败。

## 3. A↔D：事务内计时组件（可立即开发）

固定代码 [clock_ports.py](../../../../src/uaw/run/clock_ports.py)：

```python
# D新增 src/uaw/run/execution_clock.py，暴露以下类；既有构造器不改。
ExecutionClocks(records: PostgresRecordStore, *, effects: ClockIdlePort,
                now: Callable[[], str] = timestamp)
async current(actor: Principal, run_id: str) -> RunExecutionClock
async change(tx: RecordTransaction, actor: Principal, run_id: str,
             request: ClockChange) -> RunExecutionClock
# ClockChange(expected_clock_revision, mode,
#             in_flight_refs: tuple[Ref,...]=(), waiting_item_ref: Ref|None=None)
# ClockIdlePort.check(tx, actor, run_id) -> None；失败抛DomainError
```

`current`与已有ExecutionClockPort一致，读取当前原owner/conversation/Run/protocol/input/clock，返回严格RunExecutionClock；不领取时间、不修改ctx/权限、没有旧协议时明确不可用。读取不是执行授权，即使原墙钟deadline已过仍可查看合法等待。

`change`只加入A已持有 `conversation:<原id>` 的同一RecordTransaction，核对tx.owner/user、实际会话/Run/协议/clock与CAS和clock_ref；写clock及协议binding的clock_ref/revision，**不改Run/input_revision/completion_mode/任务/预算/调用/授权/队列，不commit也不另开事务**。A更新其他binding字段时重读当前row，避免拿旧payload覆盖D的clock_ref。D不得在构造器中启动进程或网络。

命名空间：`run.execution_clocks`/`run.protocol_bindings`，键均run_id，schema分别RunExecutionClock/ConversationProtocolBinding；clock_ref为checkpoint/run_id/真实clock修订。现有A admission创建revision1，D负责后续变更；A集成时替换原conversation_entry内的手写计时变更，D不改该文件。旧快照继续旧流程。

状态策略：

1. active→active只结算已耗主动段并开新段，不重领原限额；active→waiting必须有当前具体open问题及原稳定Item、Run等待状态，request在途引用为空，且**调用必需effects.check验证完整实际账本**。依赖未装配不能暂停。A的真实Idle adapter本轮M1交付；D独立组件可注入明确标记受控的库存Reader测试，不宣称生产idle已验。
2. waiting→active结算等待段，剩余主动额度不增加；不得在旧问题仍open时恢复。原问题已answered/stale/cancelled的消费规则由A同域提交；D复核当前记录，不凭传入文本判断。续跑的模型/政策/附件/费用/取消/租约准入由A负责，clock变active本身不授权执行。
3. active/waiting→stopped如实结算；stopped不得变active/waiting。原in_flight_refs即使停止也保留，不能谎称外部效果消失。取消/终态可停止但不能继续。
4. UTC服务时间、整数毫秒、拒绝时间倒退；不吞负数、不截掉真实超额。进程崩溃按持久segment恢复，重复expected_revision冲突，外层同幂等请求重放不再计时。原上限immutable，等待可长于原主动时限，原Model/Tool/15秒/90秒/审批/root有效期都不延长。
5. D不派生任何执行授权deadline。A对尚未发出的新调用按剩余额度构造新段；既有invocation及ctx原值不改。A负责兼容Budget原字段与实际lease，整链未过前不得声称已实现长等待续跑。

失败范围：缺owner/Run为所属域404，非user/归属不符403，旧协议或缺effects依赖503，CAS/非法状态409，来源/时间倒退412，主动额度耗尽409。报错不部分写clock/binding；外围事务回滚由真实SQL验证。

## 4. C→A：离线评测消费边界

C提供独立只读CLI `ops/evaluate_conversation.py`：

```text
--suite <suite.json> --manifest <manifest.json>
--observations <observations.jsonl> --reviews <reviews.jsonl>
--output <new-report.json>
```

首个里程碑由C提交严格文件schema/类型/样例及阶段SHA，字段统一冻结于其`src/uaw/evaluation/contracts.py`，不另加公开HTTP DTO。A从真实owning记录导出这些文件并消费报告，工具/Runner/模型生产装配不引用评测内部类型。C的受控fixtures可独立完成M1–M3；实际候选/基线固定来源与真实用量由A提供，未到不影响harness开发，M4只如实注明实测pending。

要求manifest固定源码/dirty状态、提示词与样本hash、固定模型配置及时间；observation含完整attempt与实际决策/文本/工具或成果证据和主动/墙钟时间；review绑定原输出hash与样本版本，明确人工核对、证据审查或模型建议，缺人工批准不伪造人工评分。所有失败/重试/未知费用纳入报告；无Reviewer为N/A，不能当零漏判。关键事实以完整来源语义审查，字符串/关键词只能筛查，不能判定正确。

C不发真实模型请求、不重放写操作、不读A凭据/本人会话；CLI输入路径属于开发者明确提供的离线文件，不扩用户本机权限。

## 5. 谁提供什么、何时有真实服务

A现在提供：已提交的0.2对象/发现端点合同、原单调用代码、准确clock Python port、明确包归属。A M1提供原账本Idle adapter与read/control服务阶段SHA；M2提供真实新服务端口/版本/运行操作示例，保留H01-v5不热改。B真实联调使用该源；会话凭据仅经受保护环境/原Page，不写进文档。D只接真实A库存及当前授权来源；C的实际候选导出到达即评测。

任何未过门槛保持pending；阶段SHA到即审，不等待三个最终包。业务错误回原worker，不由A写其业务文件。
