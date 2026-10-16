# MS-I2m A3：补充输入的实际生效证据与旧失败隔离

2026-10-16，Session A / integration。本段继续原 M2，固定阶段 SHA/标签见 DISPATCH。没有新增 worker 包。

## 1. 本段完成什么

`ConversationApplications.consume(output_ref, ctx)` 只接受原 owning 模型返回：同一用户、会话、Run、任务、操作和 attempt；原调用必须 finished/ok，原请求摘要、固定 Context、输入版本、Agent 操作与 FirstDecision 全部一致。原文及全部补充引用逐项核对，仍 accepted 的补充才改为 applied。

同一个会话事务写入补充状态、不可变 `RunInputApplication`、Run 修订及 Outbox。重复读取原结果复用回执；事务失败全部回滚，原模型调用及费用记录保留。再次读取原结果可以补交生效证据，不重发模型。这里的 applied 仅指输入被实际模型消费，不表示答案正确、工具完成、成果通过或用户接受。

原 `RegisteredAgentModels` 读取结果时复查实际快照 epoch。旧模型调用不能因当前 TaskFrame 已更新而被重新标成新输入版本的回答。无补充的普通交流不创建应用证据或额外模型调用。

## 2. 并发纠正与取消

用户在旧模型运行中提交纠正后，原输入、模型输出、失败和账本保留。`ConversationControls.pending_since` 从已提交原 TaskFrame 版本及实际追加输入证明：当前还有比该作业更晚的 accepted 输入。

`BackgroundAgent.failure` 不再把这种旧失败显示成新要求的失败；原 blocked 作业及 failure 仍保留。`RunTerminationController` 也不让旧尝试直接终结新输入。这两处不清除未知效果、领取新预算、恢复时钟或唤醒队列。用户取消优先；当前输入版本自己的失败仍按原规则终结。

## 3. 计时边界

回归发现：受控测试直接准备新版本并调用模型，没有恢复原时钟，发布端访问不存在的 active_since。已改为明确 `conversation_active_clock_required` 停点，并在写消息前检查；失败事务不产生半条回答。

这项修复不制造时钟恢复，不代写 D 的 `execution_clock.py`，也不延长任何原 Model/Tool/审批/root/native 期限。D 的真实组件和 A 的可信剩余主动段、队列唤醒尚待接线，完整同 Run 续跑未验收。

## 4. 文件与消费方式

| 文件 | 职责 |
| --- | --- |
| `src/uaw/run/conversation_applications.py` | 实际消费证明、应用状态和事件的同事务提交 |
| `src/uaw/agent/adapters.py` | 原模型快照版本检查与证据提交 |
| `src/uaw/run/conversation_control.py` | 当前 accepted 补充与原作业版本关系 |
| `src/uaw/run/background.py`、`termination.py` | 旧尝试失败的显示与终态隔离 |
| `src/uaw/run/conversation_entry.py` | 发布前必须存在真实 active 时钟 |
| `contracts/conversation_catalog.py` | 新增内部 RunInputApplication，原 1402 类型不变 |
| `contracts/build_interfaces.py` | 新内部对象的可验证结构样例 |

B 仍按五个既定 HTTP 读回 `RunContinuationReceipt.patch.state`。不根据消息文本、入队或 accepted 推断 applied。刷新查询能读到实际提交后的状态；本段没有额外 HTTP，也没有发布新的 localhost 入口。

D 的 ClockChange/ConversationClockPort、真实 RunIdleEffects 与分工保持。C 的离线评测仍是独立版本质量门槛。本轮 B/C/D 阶段尚未收到，不据远端旧分支位置推断完成。

## 5. 验证与限制

27 个不同 SQL 节点＋54 个单元节点最终通过，共 81 个；最后补充原调用摘要/模型来源约束后，受影响的 4 个 SQL 节点再次通过，不重复计数。226 源码文件 Mypy、8 个改动运行/测试文件 Ruff/格式通过；两个契约生成源通过编译，1403 正例/336 反例通过，原 1402 个结构逐项一致。

实际命令、节点及原失败见 [机器回执](evidence/ms-i2m-a3.json)。所有 SQL 使用 A 的独立开发库、随机测试用户和受控模型 HTTP 返回；不计作真实 DeepSeek 或事实质量验收。这是受影响模块回归，未重跑全仓或更新 last_full。

保留首次发布计时失败、旧失败处理回归及结构样例重复引用失败；修复后以逐节点最终回执为准。原 H01-v5 服务、本人历史、pending 费用、旧标签和 last_full 未改。

下一步仍属于原 M2：消费 D 的真实时钟阶段；建立新执行段的可信准入、原作业租约/来源复查与安全唤醒；接实际 B 页面后再运行固定模型和 H02 本人体验。现有原调用和 unknown 只对账，不重发。
