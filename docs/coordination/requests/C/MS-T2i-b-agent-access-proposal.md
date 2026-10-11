# MS-T2i-b：A 每 Run 原组件接线的最小缺口

2026-10-11。固定执行 A8 `06ff3ef56b68d391387bc7b154fa58ecb00571f9`。本提案只说明 A 所属组装的具体缺口，C不修改公共源码/DTO/flags；C路由源码阶段 f80ca330fc8a6817b98d55f6c8ce042f2f2a49ad。

## 原签名证据

`src/uaw/composition.py:531 assemble_file_tool(...)` 和 `:598 assemble_office_tools(...)` 从 `container.tool_access` 取得 access，同时用于 ToolApprovalAuthority 与 ToolInvocation。签名没有额外 `effective_agent_access`。`src/uaw/infrastructure/installed_files.py:194 assemble_installed_file(...)` 直接委托 assemble_file_tool，没有单独的每 Agent access 输入。A8 FileToolBindings 提供 facade/ledger/approvals/receipts/executor/materials，没有 results；OfficeToolBindings 有 results。

## 最小变更与消费影响

A 可给原组装函数新增显式 keyword `invocation_access: ToolAccessPort | None = None`（具体命名由A定），生产 routed 模式由实际每 Run/Agent有效来源传入同一个对象，构造 `ToolInvocation(access=invocation_access)`；兼容原独立路径可以保留旧默认。基础 Run configuration/authority/data sources仍归原-owning服务检查，Agent有效access额外限制不能被默认Run对象替代；不要简单全局替换 container.tool_access，RegisteredFileDataAccess依赖其真实 Run sources，不能换成不兼容缩窄port。若选择另一构造方式，必须满足相同当前权限及 identity不变量。

传递路径：Agent每Run来源 -> office/file/installed-file原组装 -> 原ToolInvocation -> RoutedToolRuntime(access=同一对象)。C constructor严格 `facade.invocation.access is access`，不同但看似等价的 port 也拒绝，不偷偷修补已构造 facade。Agent/composition/installed sources只由A修改。

规范结果 Reader 可以直接从 FileToolBindings.facade.invocation.results 取得既有 ToolResults 并检查其 read_result callable；A也可显式在 FileToolBindings暴露该既有对象，不能重建发布链。本项不需要共享DTO。

A使用同一个原 records store实例构造不同 ToolLedgers，C只要求 store identity，不要求ledger对象identity；routes全量Tool/provider Ref/hash要与同registry固定注册一致。若生产 reader/approval/native来源缺失，仍明确不可用。

预期行为：普通新调用仍执行原有效权限/审批/预算/一次发送；Agent拒绝时即使基础Run可用也不发送。原attempt恢复只按ledger选owning reader，当前正文读与独立原费用协调分开；没有新open/dispatch/reserve。没有公共 schema、依赖或flags变更请求，也不承诺native/模型/Task整链通过。
