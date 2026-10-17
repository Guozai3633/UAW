# A7 最新消费结论：实际组件汇合已验，固定发布按DISPATCH

2026-10-17。B/C/D最终包和D目录定向修复均已普通合入，原构造与A/D ports不变。**314不同节点通过**，实际D+原队列严格跨墙钟与两次等待、原事务回滚均有真实SQL回执；模型回复/服务时间仍受控。[逐包门槛与SHA](MS-I2m-A7-worker-acceptance.md) · [最终回执](../../../implementation/evidence/ms-i2m-a7-integration.json)。

A7补充的新ToolDispatchTimingPort及RunToolDispatchTiming准确签名见下方第1节；Tool原claim/新审批尚未消费，无默认权限或期限变化。候选服务要在start前显式装配真实ExecutionClocks与ExecutionSegments，H01-v5不热改。旧调用/审批/native期限与unknown对账规则保持。

准确固定A7 source/tag以远端DISPATCH随后正式记录为准；以下“待审批/尚未汇合”段落保留为早期停止点历史。worker原已交付包不自动扩包，无需为取文档合浮动integration。A下一步提供实际新服务/原Page、真实固定模型记录与C离线导出，不能把当前工程回执当人审/模型质量。

# A7 内部时间接口与本地集成状态

2026-10-17。**未正式发布 A7 标签；worker 继续准确 A6 与各自原阶段，不据此合浮动 integration。**

A 自有源码 `096be27` 已本地提交；B M1、D M1/M2 已普通合入本地 `5815c2abcffbf1f7110a8a273580bffd9573144f`。当前新增真实 D 汇合测试及本说明尚在工作区，数据库汇合和新固定发布待自动审批服务恢复。见[实现与准确门槛](../../../implementation/MS-I2m-A7.md)。

## 1. 精确协议

```python
from uaw.shared.tool_timing import ToolDispatchTimingPort
from uaw.run.tool_timing import RunToolDispatchTiming
from uaw.run.execution_segments import ExecutionSegments

timing: ToolDispatchTimingPort = RunToolDispatchTiming(
    original_records, segments=ExecutionSegments(original_records)
)
# 未来 Tool 原 worker 在原 claim 的同一个 RecordTransaction 中消费：
assert await timing.check(original_tx, original_trusted_context) is None
```

`check(tx: RecordTransaction, ctx: TrustedExecutionContext) -> None`。不接受 deadline override、模型建议的取消状态或传入 ledger 快照。没有 segments 注入时只允许原期限；有注入也必须证明实际段来源，不能续期旧 context。返回非 None、来源缺失或任何异常不得 fallback。

来源必须同 owner、同实际数据库/AsyncSession 和当前活跃事务；上下文归属原 conversation/task/Run。适配器内部获取原 conversation 事务锁并刷新当前来源；调用方若已持有 tool-run 锁，顺序必须为 tool-run→conversation。conversation 锁中不得反向获取 tool-run，不能在这段等待模型/外部能力或另开事务。

该检查只证明“此刻当前调用的时间来源”。Tool 原访问权限、审批有效期、参数/资源、budget reservation/原 attempt 期限、一次发送及 unknown 对账继续独立执行。适配器本身不写入或发送，也不决定 Agent 选择哪个工具。

## 2. 当前未消费与后续分工

ToolLedger 构造及实际 claim 未改，本段不声称 Tool 跨墙钟已可用。新审批仍有原 ledger 上界，也尚未消费新段；旧审批有效期不可变。C/MS-E1 仍只开发独立评测，没有自动获得 Tool 源码范围。后续明确原 worker 的范围和验证清单后再接消费端。

B 继续原 MS-U4，D 继续原 MS-K1 M3/M4。A7 修复的是 A 的恢复入口条件，D 当前构造器不变；A 在自己的原队列/Model/Context/Artifact 场景消费真实 D，不能由 D 时钟测试代替 A 汇合验收。

## 3. 当前验证与停止点

已通过21不同 SQL＋14代理单元，233源码严格类型和A变动文件静态检查通过。真实 D 汇合三个测试已准备，自动审批因额度限制未完成审查，命令未执行；B 前端 A 复跑、新服务与实际模型仍 pending。

不发布虚构 A7 SHA，不要求 worker 同步未发布版本；原 A6 标签、共同开工标签和 H01-v5 保留。通过后由 A 发布固定源码、逐包接受及具体新服务输入。
