# MS-I2m A4 固定接线说明

2026-10-16，源码 **4102911b3bd493ca73d2e2a3c76c35017e86a5b7** / **ms-i2m-a4-source**。共同基线和四个包的 M1–M4 保持，不新拆包。

## A 的恢复入口

新增内部入口 `BackgroundAgent.resume_conversation(original_actor, run_id) -> bool`。它使用原 `prepare()` 得到的同一 RunJobs 与实际 records，经过完整认证、固定模型/政策/角色和原库存复查，调用 ConversationResumer。没有 D clock 时明确 503，不是权限开关。

将来在**一次性候选组装**中注入已审阅的真实来源：

```python
driver = BackgroundAgent(container, conversation_clocks=actual_execution_clocks)
jobs = await driver.prepare()  # 只构造本实例的一套队列，不在现有服务重复 prepare
await driver.resume_conversation(original_authenticated_actor, run_id)
```

`actual_execution_clocks` 必须是 D 的真实组件及 RunIdleEffects。当前 Container.start/HTTP 未自动装配此源，不能复制测试 clock 当生产依赖。恢复器只允许原墙钟期限内的续跑；超时仍拒绝。原预算/调用/审批/root 不续期。

## D 消费边界

ClockChange/ConversationClockPort 构造与签名原字节不变。A 在原会话事务内先写 Run preparing，再发 active；发布消息/问题时同事务先写 completed/waiting，再发 stopped/waiting_for_user。D 只更新原 clock 与 binding.clock_ref/revision，不改 Run/input/队列/预算或另开事务。

A 检查实际 row 与返回、一次修订、限额不增、消耗不减、当前 binding 与原 Run。队列容量、等待后当前认证/政策失败都使同事务回滚。A 已修复原兼容路径 clock_ref 多加 1 和 Run 事件修订问题；历史本人记录没有热修或迁移。

D 实际阶段到达后 A 审阅接线，继续做新执行段、取消/正式成果计时收尾及实际持久恢复。受控 seam 只证明 A 消费，不能作为 D 计时验收。

## B/C 当前消费

五个控制 HTTP、0.2 meta、RunContinuationReceipt/RunConversationView 不改；受理仍与 applied/完成/用户接受区分。本段无新服务 URL/本人认证来源，不把 H01-v5 的旧服务当作本段整链。B 继续原允许目录和本包余下里程碑。

C 的实际候选导出与固定模型质量门槛仍 pending；本段没有真实模型新调用或新费用。C 可继续原独立评测设施，不据 A 的受控模型输出补写人工评分。

## 固定来源与回执

28 个不同 SQL 节点最终通过，原首次 2 个失败及定向复跑保留；227 源码类型、5 文件 Ruff/格式通过。详见 [实施范围](../../../implementation/MS-I2m-A4.md) 和 [回执](../../../implementation/evidence/ms-i2m-a4.json)。没有新全仓/实际模型/本人体验通过声明。

需要本阶段的 worker 按既定流程先提交自身阶段并保持干净，fetch 核对远端 DISPATCH/准确 tag 后普通 merge 固定 `ms-i2m-a4-source`，保留原提交。A 不操作 worker 分支/工作区；不合浮动 integration、不 reset/rebase，不移动旧标签。
