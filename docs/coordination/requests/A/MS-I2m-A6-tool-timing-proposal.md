# A6：Tool 跨原墙钟的时间来源提案（尚未安装）

2026-10-16，A。当前 C/MS-E1 允许范围是独立质量评测；本提案**不扩大 C 任务范围、不要求自动改 Tool**。原 Tool 源码和业务归属保留，后续明确任务再消费。

## 已确认的具体缺口

`src/uaw/tool/ledger.py` 的实际 dispatch claim 仍检查 `min(ctx.deadline, RootBudgetLedger.deadline)`。A6 的新段保持原 ledger.deadline 原字节，因此跨原墙钟的 Tool 动作仍会拒绝。已有动作/预留/审批的原截止时间和 unknown 恢复规则继续有效；这不是已经支持跨原墙钟工具的声明。

## 建议的边界

1. Tool 使用必须显式注入的内部时间 port，在原 claim 事务内读取原当前 Run、ledger 与 A 的执行段，返回当前动作可用的时间上界；默认缺失仍走原 deadline，不能把 ledger 改写成延长期限。
2. A 适配器调用 `ExecutionSegments.deadline(ctx, actual_run, actual_ledger, tx=original_tx)`，完整复核原历史作业/时钟、当前 binding、完整主体和 scope。时间结果不替代原 ToolAccess、审批、参数/资源 Reader、预算 reservation 或效果账本。
3. 新动作只能使用尚未发送的新上下文；Tool 已存的原 context/deadline、原审批有效期、Runner command/lease/root/device 仍各自检查。unknown 查询原回执，不重新 claim 或换 attempt 重发。
4. 要验证：缺 port/缺段拒绝、等待后权限撤销、当前段耗尽、旧审批过期、同动作幂等、参数版本变化、原 unknown 不重发，以及外层事务回滚。

本提案不修改公开接口、工具目录、feature flags 或旧记录。精确构造/签名需与 Tool 原 worker 审核后由 A 发布独立固定接口阶段；本轮暂不生成第二套 Tool schema 或宽泛的 deadline override 参数。
