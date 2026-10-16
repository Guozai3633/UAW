# MS-I2m A3 固定消费说明

2026-10-16。源码 **63bf7aaeedb0cbca2dd7198a8f4fd4fc2c2cfb7b**，不可变标签 **ms-i2m-a3-source**。共同开工标签、原四包和目录归属保持。

## A：已安装与仍待装配

原 `RegisteredAgentModels.read` 已接 `ConversationApplications.consume`。它从原 ModelInvocation、完整请求及可信 Context 摘要、实际 ContextSnapshot/准备记录、当前输入/补充、LoopOperation 和 FirstDecision 建立应用证据。新补充只有被真实模型消费才 applied；证据、补充、Run 修订和事件同事务提交。旧模型快照与新输入版本不符即拒绝。

旧尝试失败的可见性与独立终态处理已按实际输入版本隔离；原错误、输出、用量仍保存，取消仍优先。等待时钟不能发布新回答，明确返回 `conversation_active_clock_required`，没有自动补时钟、续期或重发。

本段是原 M2 子段；队列唤醒、剩余主动执行段、真实 D 时钟和新服务尚未安装，H02 未接受。81 个不同节点通过＝27 SQL＋54 单元，最后加固后的 4 SQL 已复跑，不重复计数。详见 [实施范围](../../../implementation/MS-I2m-A3.md) 和 [完整证据](../../../implementation/evidence/ms-i2m-a3.json)。

## B：刷新与生效显示

五个 HTTP 和请求字段不变。原 `RunContinuationReceipt.patch.state == applied` 来自实际模型消费，不是前端在 accepted 后自行推进。读取 `/v1/runs/{run_id}/continuations/{request_id}` 获取最新回执，或读取原 ConversationView 的当前 Run/CAS。应用证据提交会增加 Run 修订，提交新控制前应重读当前版本。

applied 不表示已完成任务、核验通过或用户接受；页面保留原状态与成果独立显示。本段没有新的服务 URL/认证来源，不替换 H01-v5。

## D：计时装配边界

ClockChange、ConversationClockPort、RunIdleEffects 的既定签名不变。D 仍只写专属 clock 与 binding.clock_ref，加入 A 的原会话事务；不写 Run/队列/输入/预算。A 在恢复后发布回答前要求实际 active 时钟；A 仍负责尚未发送调用的可信执行段与旧期限兼容。不可用受控时钟代替生产来源。

## C：离线质量

本段没有真实模型或新候选导出，不证明事实正确性。后续实际观测应区分输入受理、实际使用、结果输出和成果接受；原 owning 输出和全部用量仍是报告来源。

## 阶段同步

需要本阶段的 worker 先提交自己的阶段并保持工作区干净，自行 fetch 核对远端 DISPATCH 与准确标签，再普通 merge `ms-i2m-a3-source` 保留原提交。只消费需要的固定阶段，不合浮动 integration，不 reset/rebase，不重写原 handoff。A 不替 worker 切分支或同步；原 M1–M4 继续，不新拆小包。
