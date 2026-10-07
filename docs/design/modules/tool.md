# 工具执行 · Tool：模块开发设计

节点 `tool` · UAW v0.10 · 2026-10-07 · 状态：目标设计，Runtime 未实现。

[开发设计索引](../README.md) · [目录设计](../../PROJECT_STRUCTURE.md) · [公共契约](../COMMON_CONTRACTS.md)

## 统一入口与状态所有权

计划包：`src/uaw/tool/`，入口：`src/uaw/tool/facade.py`。

入口契约：`ToolRuntime.discover(DiscoveryRequest)、invoke(ToolCall)、reconcile(ReconcileRequest)`。

所有权：ToolSpec、调用attempt/效果账本、提供方健康与MCP协议session。

## 内部组织策略

发现支路缩小候选并向LLM暴露schema；调用支路校参数→预检→必要审批→复核→意图→派发→规范结果。失败恢复有界且只自动切明确等价能力。MCP和内部控制工具均经过同一闸门。

facade接收可信请求并协调子组件；子组件不直接调用其他Runtime的私有实现。只通过注入的port调用邻域公开入口。Python首阶段组合在同一进程内，持久化和本地Runner执行仍通过边界接口。

## 数据与依赖接口

输入：工具参数与可信 ToolRuntimeContext。输出：ToolResult、效果状态、原始结果引用。

注入ports：`ConfigurationReader、ApprovalPort、BudgetPort、Workspace/Agent/Context/Model控制工具适配器、ProviderAdapters、EffectRepository`。

领域类型放本包 contracts.py；模型可见工具schema由Tool消费。Repository不暴露其他模块可任意写本模块对象的方法，修改必须走本模块业务入口。

## 决策、权限与资源策略

选择哪个工具由Agent当前模型决定；注册、发现过滤、闸门、重试/熔断与对账由代码。非等价替换反馈Agent再判断。

未知写结果先核对；只有登记等价契约才自动切换。

每次提交绑定真实版本、当前scope、剩余deadline和预算。固定常规配置与当前撤销分开检查。多模块提交用本地事务或可恢复意图，不能承诺外部动作exactly-once。

## 失败与恢复策略

facade保留失败发生阶段与原始受控引用。参数/依赖/版本冲突回调用者修复；拒绝不通过换工具绕过；副作用unknown先Tool对账。恢复先检查此领域schema/版本兼容，再恢复可继续边界，不用Trace重建权威状态。

## 文件组织规则

- `facade.py`：统一入口、依赖注入、调用编排。
- `contracts.py`：领域请求/结果/版本化对象。
- `ports.py`：存储、跨Runtime与执行器协议。
- 子组件文件/包：实现具体策略，分层节点有自己的facade/contracts/ports。
- `repository.py`：领域存储适配，实现CAS和幂等；业务规则仍在组件。
- `tests/unit/` 与 `tests/integration/`：实现阶段只验证具体风险/门槛，不复制实现。

## 实施与验收门槛

schema与权限分离，审批后资源变更复核，未知写先查状态，MCP撤销与大结果分页。

首条真实任务贯通入口/核心子组件；其他节点先保留port，未实现能力不暴露为可调用工具。细分模块策略与验收案例见下面各文档。

## 逐字段接口与对象定义

[本节点全部接口](../../api/nodes/tool.md) · [统一对象字典](../../api/OBJECTS.md) · [接口共同规则](../../api/CONVENTIONS.md)

上面的领域字段用于说明策略。准确请求DTO、动作分支、必填性、返回对象和结构规则以接口契约源contracts/interface_catalog.py及其生成schema为准；语义/权限/版本/执行策略仍按本设计落实。出现差异需同时修维护源，不能拿摘要字段替代当前接口校验。

## 内部模块与目录

| 子模块 | 详细开发策略 | 计划代码文件 |
| --- | --- | --- |
| 工具注册与版本 | [tool.registry](../components/tool-registry.md) | `src/uaw/tool/registry.py` |
| 工具发现与筛选 | [tool.discovery](../components/tool-discovery.md) | `src/uaw/tool/discovery.py` |
| 调用闸门与派发 | [tool.invocation](../components/tool-invocation.md) | `src/uaw/tool/invocation/facade.py` |
| 调用与副作用账本 | [tool.effects](../components/tool-effects.md) | `src/uaw/tool/effects.py` |
| 失败恢复与等价切换 | [tool.failure](../components/tool-failure.md) | `src/uaw/tool/failure.py` |
| MCP 连接与适配 | [tool.mcp](../components/tool-mcp.md) | `src/uaw/tool/mcp/facade.py` |
| 领域与外部适配器 | [tool.adapters](../components/tool-adapters.md) | `src/uaw/tool/adapters.py` |
| 结果规范化与分页 | [tool.results](../components/tool-results.md) | `src/uaw/tool/results.py` |
| 执行审计与指标 | [tool.audit](../components/tool-audit.md) | `src/uaw/tool/audit.py` |

## 模块联系

| 方向 | 关系与载荷 | 对应设计 |
| --- | --- | --- |
| 上游 → 本节点 | 调用：发现/执行动作 | [决策执行 · Agent](agent.md) |
| 本节点 → 下游 | 调用：受控文件/环境/进程 | [工作区 · Workspace](workspace.md) |
| 本节点 → 下游 | 调用：定义/委派等控制工具 | [决策执行 · Agent](agent.md) |
| 本节点 → 下游 | 调用：资料/引用等控制工具 | [上下文 · Context](context.md) |
| 本节点 → 下游 | 数据/引用：实际结果/类型化失败 | [决策执行 · Agent](agent.md) |
| 本节点 → 下游 | 状态/事件：审批请求与用量 | [运行控制 · Run](run.md) |
| 上游 → 本节点 | 权限/配置：提供方与当前撤销 | [共享支撑与控制层](support.md) |

## 参考与需要验证的选择

- [Tool · 调用/MCP/效果](https://app.notion.com/p/3e96ccd32c8780fab75dd0b4c21fe7fb)：参考问题与原则，具体协议为 UAW 自己的设计。
- [Guardrails · 审批/复核](https://app.notion.com/p/3f06ccd32c878056b729e7a41fd4232b)：参考问题与原则，具体协议为 UAW 自己的设计。

题集是检查遗漏的来源，未逐题验证第三方技术结论。实施阶段涉及具体供应商协议时再核对其官方资料；本文的字段、算法顺序与权限边界不是从题集自动取得的事实。

