# MS-I2m A6：固定执行段来源与接线

2026-10-16，固定源码 **b16c69a92d81124c00fb859ce8123748f56df054** / **ms-i2m-a6-source**。原共同基线及 B/MS-U4、C/MS-E1、D/MS-K1 连续 M1–M4 不变，未发布新 worker 包。

## A 的新组件

`ExecutionSegments(records)` 位于 `src/uaw/run/execution_segments.py`。它在 A4 的同一安全唤醒事务中，消费 D 实际 active clock，保存 `InternalRunActiveSegment`，然后在同一次作业 CAS 保存新上下文。旧上下文与原调用保留；没有改写 Run.budget、RootBudgetLedger.deadline 或总额度。

新调用上界由实际 `captured_at + active_limit_ms - active_elapsed_ms` 派生。超出原墙钟时，预算/权限/上下文/消息/文本成果复查原作业和时钟历史摘要、当前 clock pin、原预算和首次准入上限。旧上下文不能使用新期限，缺来源按原截止时间拒绝。

当前身份/模型/角色/政策观察与执行授权分开：`inspect_for_continuation()` 只返回 None，不能交给模型或 Tool 当授权快照；原 `resolve()` 保留实际期限检查。

## D 到达后的显式装配

固定 `ClockChange`、`ConversationClockPort`、`ClockIdlePort` 字节不变。D 继续原 MS-K1；A6 不修改 D 的业务实现、测试或分支。

以下示例以 **D 的真实组件已接受并合入** 为前提。当前默认两项均未注入，不是已有新服务入口。

```python
from uaw.run.clock_sources import RunIdleEffects
from uaw.run.execution_clock import ExecutionClocks  # D 真实阶段合入后才存在
from uaw.run.execution_segments import ExecutionSegments

assert container.records is not None
container.conversation_clocks = ExecutionClocks(
    container.records, effects=RunIdleEffects()
)
container.conversation_segments = ExecutionSegments(container.records)
await container.start()  # 独立新候选实例，不热改 H01-v5
```

只注入 clock 而没有 segments 时，沿用 A4/A5 原截止时间恢复。只注入 segments 没有实际 clock 时无法恢复，不能凭空签发新段。D 只改 clock/binding，A 负责新段、队列和消费者；D 不续期任何原调用、审批或 native 来源。

## B/C 消费与 Tool 缺口

五个控制 HTTP、0.2 meta 和原 1403 schema 不变；唯一新增的是服务端内部执行段结构。B 继续现有公开回执和 Item，尚无本段新服务 URL。C 继续独立评测设施，本段输出是受控 HTTP 测试数据，不作为实际 DeepSeek 或人工事实评分。

ToolLedger 的实际 claim 仍绑定原账本 deadline，因此跨原墙钟的 Tool 动作暂时拒绝。[具名提案](MS-I2m-A6-tool-timing-proposal.md)说明内部 time port 的接线要求；C 当前 MS-E1 不因此扩包或修改 Tool。原审批、预留、模型/Runner 调用和目录授权期限继续独立检查，unknown 不重发。

## 精确验证与同步

最终 **83 SQL＋56 契约单元，139 个不同节点通过**。原对话整批 51 项中 50 通过、1 个租约测试 CAS 使用旧修订而失败；该原节点改为核对已持久化过期状态及实际修订后，定向复跑通过。另 32 项权限/租约/预算通过。所有初次、诊断和重复节点保留且不重复相加。

230 源码类型、13 变动源码/测试文件 Ruff/格式通过；1404 正例/336 反例通过，原 1403 结构逐项不变。详见 [实施范围](../../../implementation/MS-I2m-A6.md) 和 [完整机器回执](../../../implementation/evidence/ms-i2m-a6.json)。没有实际 D 计量、真实长等待、固定模型质量或本人 H02 的通过声明；没有实际模型新费用或新全仓门槛。

需要本阶段的 worker 先提交自身阶段并保持干净，自行 fetch 核对远端 DISPATCH 和准确 tag 后普通 merge 固定 `ms-i2m-a6-source`，保留原提交；不合浮动 integration，不 reset/rebase。A 不同步 worker 分支，不代写其业务。阶段到即审阅，不等待三个最终包齐备。
