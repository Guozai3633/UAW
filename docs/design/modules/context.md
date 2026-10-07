# 上下文 · Context：模块开发设计

节点 `context` · UAW v0.10 · 2026-10-07 · 状态：目标设计，Runtime 未实现。

[开发设计索引](../README.md) · [目录设计](../../PROJECT_STRUCTURE.md) · [公共契约](../COMMON_CONTRACTS.md)

## 统一入口与状态所有权

计划包：`src/uaw/context/`，入口：`src/uaw/context/facade.py`。

入口契约：`ContextRuntime.build(ContextRequest)、ingest(IngestionRequest)、remember(MemoryWriteRequest)、forget(ForgetRequest)`。

所有权：ContextSnapshot/Manifest、Task资料派生索引、Memory版本和Reference/Citation。

## 内部组织策略

来源/规则、资料索引、记忆是独立支路；按purpose与模型预算合流。来源经授权解析、版本发布后检索；记忆候选经用途/冲突核验；选择/压缩保护关键要求；Composer生成当前调用快照。

facade接收可信请求并协调子组件；子组件不直接调用其他Runtime的私有实现。只通过注入的port调用邻域公开入口。Python首阶段组合在同一进程内，持久化和本地Runner执行仍通过边界接口。

## 数据与依赖接口

输入：purpose、目标、作用域、版本、token预算。输出：ContextSnapshot / ContextManifest / Reference。

注入ports：`HistoryReader、BoardReader、WorkspaceReader、SourceProvider、ModelFacade、CachePort、Index/Memory/ReferenceRepository`。

领域类型放本包 contracts.py；模型可见工具schema由Tool消费。Repository不暴露其他模块可任意写本模块对象的方法，修改必须走本模块业务入口。

## 决策、权限与资源策略

查询生成/语义选择/记忆提炼/压缩按需使用当前模型；结构解析、访问过滤、版本发布与删除由代码执行。embedding模型是独立工具能力。

压缩不赋权；资料和规则按信任来源区分。

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

真实材料定位、权限内检索、删除传播、关键数字压缩保护及输出空间保留。

首条真实任务贯通入口/核心子组件；其他节点先保留port，未实现能力不暴露为可调用工具。细分模块策略与验收案例见下面各文档。

## 逐字段接口与对象定义

[本节点全部接口](../../api/nodes/context.md) · [统一对象字典](../../api/OBJECTS.md) · [接口共同规则](../../api/CONVENTIONS.md)

上面的领域字段用于说明策略。准确请求DTO、动作分支、必填性、返回对象和结构规则以接口契约源contracts/interface_catalog.py及其生成schema为准；语义/权限/版本/执行策略仍按本设计落实。出现差异需同时修维护源，不能拿摘要字段替代当前接口校验。

## 内部模块与目录

| 子模块 | 详细开发策略 | 计划代码文件 |
| --- | --- | --- |
| 来源解析 | [context.sources](../components/context-sources.md) | `src/uaw/context/sources.py` |
| 规则与信任装配 | [context.rules](../components/context-rules.md) | `src/uaw/context/rules.py` |
| 摄取与索引发布 | [context.ingestion](../components/context-ingestion.md) | `src/uaw/context/ingestion.py` |
| 资料检索与证据 | [context.retrieval](../components/context-retrieval.md) | `src/uaw/context/retrieval.py` |
| 记忆生命周期 | [context.memory](../components/context-memory.md) | `src/uaw/context/memory/facade.py` |
| 选择与上下文预算 | [context.selection](../components/context-selection.md) | `src/uaw/context/selection.py` |
| 压缩与关键项保护 | [context.compression](../components/context-compression.md) | `src/uaw/context/compression.py` |
| 装配与快照 | [context.composer](../components/context-composer.md) | `src/uaw/context/composer.py` |
| 引用登记与解析 | [context.references](../components/context-references.md) | `src/uaw/context/references.py` |

## 模块联系

| 方向 | 关系与载荷 | 对应设计 |
| --- | --- | --- |
| 上游 → 本节点 | 调用：按需补充理解材料 | [任务理解 · Intent](intent.md) |
| 上游 → 本节点 | 调用：装配本轮输入 | [决策执行 · Agent](agent.md) |
| 本节点 → 下游 | 调用：需要语义压缩/摘要时 | [模型调用 · Model](model.md) |
| 上游 → 本节点 | 调用：资料/引用等控制工具 | [工具执行 · Tool](tool.md) |
| 上游 → 本节点 | 数据/引用：授权文件与产物版本 | [工作区 · Workspace](workspace.md) |
| 上游 → 本节点 | 权限/配置：资料/记忆与保留政策 | [共享支撑与控制层](support.md) |

## 参考与需要验证的选择

- [Context · 预算/压缩/选择](https://app.notion.com/p/3ec6ccd32c87802fb6c2c7dd51db660d)：参考问题与原则，具体协议为 UAW 自己的设计。
- [Memory · 冲突/删除](https://app.notion.com/p/3ec6ccd32c87803db411c4c48b832941)：参考问题与原则，具体协议为 UAW 自己的设计。
- [RAG · 更新/权限](https://app.notion.com/p/3d66ccd32c87806894a2ec48969c200a)：参考问题与原则，具体协议为 UAW 自己的设计。

题集是检查遗漏的来源，未逐题验证第三方技术结论。实施阶段涉及具体供应商协议时再核对其官方资料；本文的字段、算法顺序与权限边界不是从题集自动取得的事实。

