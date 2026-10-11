# MS-T2i-b M1/M2：严格原 Tool runtime 路由

2026-10-11，Session C，`E:/UAW/.worktrees/tool` / `dev/tool`。
执行基线 `ms-i2l-a8 / 06ff3ef56b68d391387bc7b154fa58ecb00571f9`；源码标签 `ms-i2l-a8-source / 16e0efaf6daff2fbbd0281473a8c6cc1f652d0e6`。
固定续包文档 `ms-i2l-a8-followup / 610a920d9cc83900f056b0eb2ccfaf13cb122ff8`，三标签均已 fetch 后与远端核对；仅快进执行标签。
阶段源码 **f80ca330fc8a6817b98d55f6c8ce042f2f2a49ad**。随后继续 M3/M4，不等待集成，不扩大本包。

## 固定接口与 A 构造

`uaw.tool.runtime_router` 提供固定的 `ToolResultReadPort`、冻结 `ToolRuntimeRoute`、`RoutedToolRuntime`。

```python
runtime = RoutedToolRuntime(
    registry, original_ledger,
    (
        ToolRuntimeRoute(office_tool_ref, office_provider_ref, office.facade, office.results),
        ToolRuntimeRoute(file_tool_ref, file_provider_ref, file.facade, file.results),
    ),
    access=effective_agent_access,
)
```

在构造独立 facade 时，A 必须已将同一个 `effective_agent_access` 注入每个原 `ToolInvocation(access=...)`。不是仅 facade.access，不能用 Run access 替代，路由器不修改已传入实例。所有 facade/Invocation 必须使用同 registry，所有 Invocation 和已接 Reconciler 必须共享 `original_ledger.store` 的实际实例（仅同数据库 URL 不够）。恢复重建也需显式注入该 access，即使它拒绝新执行；三个恢复入口不会调用其 snapshot。每个 results 是相应 ToolResults owning Reader，不能把 file Reader 给 office。

1–128 个完整 tuple；configuration 工具 Ref 必有 spec hash；provider Ref 精确保留版本及存在的 hash；禁止 location/access_scope 和重复 tool id/version（包括不同 hash）。缺 invocation/access/store/完整注册绑定构造时报 ValueError。执行中仍复核绑定，换 access/规格/provider 时拒绝。

五个入口：

- `discover(request, ctx) -> RuntimeToolruntimeDiscoverResult`：消费 ToolToolsDiscoverInput，当前共享 access，原 registry，仅已绑定固定 routes 参与原小目录词法过滤/评分，再有界返回 DiscoveryResult；不执行、不自动选择、不冒充语义检索。
- `invoke(request, ctx) -> RuntimeToolruntimeInvokeResult`：原 NormalizeCallRequest，JSON 冻结再 normalize 选择，原请求完整委托 facade.invoke；原 ctx/action/attempt 不改，规范参数/hash 不丢弃，无 fallback。审批/预算/一次发送仍由原 Invocation。
- `reconcile(request, ctx) -> RuntimeToolruntimeReconcileResult`：严格 ReconcileRequest，额外 receipt_ref 拒绝；从 SQL 原 attempt/call/spec/context 唯一路由原 Lookup/Reconciler。
- `read_outcome(action_id, ctx) -> ToolReconciliationReceipt`：实际接受且当前 owning Reader 可读的回执；失败抛 DomainError。
- `read_result(action_id, ctx) -> RuntimeToolruntimeInvokeResult`：原 ToolResults 的实际 ToolResult envelope；失败抛 DomainError。不把成功 envelope 当 Task 成功。

后三项核对原 attempt 的完整 ctx、原 action 的 call/spec 以及当前 registry 全规格/provider；不读新的执行 access、不 reserve/send/retry。不存在 route 返回 dependency_unavailable；旧规格/会话/attempt 变化明确拒绝。只查询唯一 owning source，不扫描提供方。完整效果/费用独立语义不改；正文 Reader 拒绝不撤销或阻断 A 原独立账务恢复入口，A仍按原持久费用计划调用原 Budget/文件账务 adapter，不能由结果失败推断未执行或零费用。

## 阶段验证 / 未完成

28 个 controlled delegation 单元通过，明确不证明真实执行/权限。ruff 通过；mypy 初次发现 discover 字典推断过窄，已显式标注 JsonObject，复验通过，原失败回执保留。
回执：ignored `tests/.artifacts/C/MS-T2i-b/M1-{unit.xml,unit.txt,ruff.txt,mypy.txt,mypy-fixed.txt}`。
M3/M4真实 55434 混合办公/file、恢复、取消/撤销和费用中断继续执行。生产 native/person approval 与 Agent/composition 接线未验收，不开放 flags/provider，也不改公共 DTO。
