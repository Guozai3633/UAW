# Model：模型政策与实际调用 · 技术组件设计

技术v0.1 · 2026-10-07 · 主选设计；实际实施范围见[开发记录](../../implementation/README.md)。

[技术总览](../../../TECHNOLOGY_STACK.md) · [模块索引](../README.md) · [框架边界](../FRAMEWORK_BOUNDARIES.md)

## 1. 主选组件与使用阶段

| 组件 | 实际包/服务 | 在本模块承担什么 | 基线与加入时机 |
| --- | --- | --- | --- |
| [Python](https://devguide.python.org/versions/) | `CPython` | 七Runtime和本地Runner语言 | 3.14.x主线；3.13仅兼容回退候选 / 基础 |
| [Pydantic](https://docs.pydantic.dev/latest/concepts/strict_mode/) | `pydantic` | 严格Python DTO与内部类型 | 2.x / 基础 |
| [JSON Schema校验器](https://python-jsonschema.readthedocs.io/en/stable/) | `jsonschema` | 执行现有2020-12契约 | 4.x / Draft202012Validator / 基础 |
| 批准提供方官方SDK | `管理员所选provider的官方Python包` | 真实文本/工具/结构输出与usage | 每provider独立冻结 / P0-05 |
| [HTTPX](https://www.python-httpx.org/async/) | `httpx` | 异步联网与连接池 | 稳定版 / P0/P2 |
| [LangChain组件](https://docs.langchain.com/oss/python/langchain/overview) | `langchain-core及选定provider集成包` | 基础抽象按框架依赖；模型/资料集成位于UAW接口之后 | 与LangGraph/SDK兼容组合 / core随依赖；provider集成按需 |
| [SQLAlchemy](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html) | `sqlalchemy` | 领域Repository与事务适配 | 2.x异步API / P0 |
| [PostgreSQL](https://www.postgresql.org/support/versioning/) | `数据库服务` | 业务状态、CAS、Outbox与持久待办 | 17.x受支持维护线 / P0 |

表中P4/P5或按需组件不要求首轮全部安装。SDK供应商、账户授权、可选环境和格式仍按产品决策/管理员配置确定；组件主选不会扩大权限。

## 2. 接入、细分职责与实现策略

### 接入方式

主路径用管理员批准提供方的官方异步SDK；没有合适SDK时用HTTPX协议adapter。LangChainProviderAdapter为按需集成选项，不是必装全部provider。任何adapter输出统一UAW的ModelResponse/usage/Ref，框架Message类型只在adapter内转换。

官方SDK具体包与endpoint依D06配置，实施时核对提供方官方协议。首次只接一个真实provider，不把‘兼容某API’自动视作支持所有工具/结构输出/缓存/usage能力。

### 模型选择与能力

ModelCatalog读已启用配置，PolicyResolver从真实会话/用户覆盖/父实例解析政策。固定模型贯穿理解、子任务、语义评审；不可用返回needs_resolution，不暗换。Auto只有明确授权集合/范围内才路由。

CapabilityValidator记录协议、上下文、结构输出、工具调用和价格版本。Pydantic/jsonschema检查模型结构输出，语义验收仍由上层负责。结构不支持可走批准的JSON提案+校验路径，不能据此偷换模型或绕权限。

### 流、预算与恢复

Gateway在调用前预留预算，把所有真实attempt、partial输出、实际模型ID/配置/价格修订记入账本。原始完整输出入BlobStore；SSE从统一InteractionItem事件产生。

SDK自动重试如可配置则关闭/统一接管；无法可靠报告真实attempt的adapter不能宣称精确成本。取消请求关闭流并处理可能已计费状态；usage缺失标pending，不能当0。部分输出失败不重复拼接。

provider前缀缓存按实际cached token/费用回执观测；稳定上下文由Context装配，不能为了缓存重排指令优先级。SDK升级与能力测试、价格配置独立版本化。

## 3. 架构子节点的具体技术落点

| 节点 | 技术组件 | 如何落地 | 策略 / 准确接口 |
| --- | --- | --- | --- |
| `model` | Python、Pydantic、JSON Schema校验器、SQLAlchemy、PostgreSQL | 自有模型继承/能力目录/价格版本与全部attempt账本 | [设计](../../design/modules/model.md) / [接口](../../api/nodes/model.md) |
| `model.catalog` | Python、Pydantic、JSON Schema校验器、SQLAlchemy、PostgreSQL | 自有模型继承/能力目录/价格版本与全部attempt账本 | [设计](../../design/components/model-catalog.md) / [接口](../../api/nodes/model.catalog.md) |
| `model.policy` | Python、Pydantic、JSON Schema校验器、SQLAlchemy、PostgreSQL | 自有模型继承/能力目录/价格版本与全部attempt账本 | [设计](../../design/components/model-policy.md) / [接口](../../api/nodes/model.policy.md) |
| `model.capability` | Python、Pydantic、JSON Schema校验器、SQLAlchemy、PostgreSQL | 自有模型继承/能力目录/价格版本与全部attempt账本 | [设计](../../design/components/model-capability.md) / [接口](../../api/nodes/model.capability.md) |
| `model.gateway` | Python、批准提供方官方SDK、HTTPX、LangChain组件 | 批准官方SDK主路径；LangChain按需隔离在adapter内 | [设计](../../design/components/model-gateway.md) / [接口](../../api/nodes/model.gateway.md) |
| `model.adapters` | Python、批准提供方官方SDK、HTTPX、LangChain组件 | 批准官方SDK主路径；LangChain按需隔离在adapter内 | [设计](../../design/components/model-adapters.md) / [接口](../../api/nodes/model.adapters.md) |
| `model.recovery` | Python、PostgreSQL | 固定模型或明确Auto集合内恢复，拒绝隐式替换 | [设计](../../design/components/model-recovery.md) / [接口](../../api/nodes/model.recovery.md) |
| `model.usage` | Python、Pydantic、JSON Schema校验器、SQLAlchemy、PostgreSQL | 自有模型继承/能力目录/价格版本与全部attempt账本 | [设计](../../design/components/model-usage.md) / [接口](../../api/nodes/model.usage.md) |

## 4. 目录与依赖位置

- `src/uaw/model/`
- `src/uaw/model/providers/`

目录为完整开发目标，部分工程设施已实现，业务能力以实际记录为准。领域contracts/ports保留UAW类型；第三方库在实现adapter中使用，composition负责组装。框架或ORM对象不能成为跨Runtime公开协议。

## 5. 对应开发轮次与验收

| 工作包 | 本轮职责 | 当前状态 |
| --- | --- | --- |
| [P0-05 固定模型真实调用与协议恢复](../../plan/rounds/P0-05.md) | 完整执行用户选择的模型，不做静默模型替换。 | in_progress |
| [P4-04 多层结果缓存与在途合并](../../plan/rounds/P4-04.md) | 在不改变当前权限和结果语义的前提下减少重复工作。 | planned |
| [P4-08 明确Auto授权与能力恢复](../../plan/rounds/P4-08.md) | 固定模型仍不变，Auto只能在用户授权范围内选择。 | planned |

关联轮次覆盖主责与协同工作，不等于每轮都实现本模块全部功能。按轮任务/具体能力附真实证据，再核对 [技术兼容与接入验证](../VALIDATION.md)。

## 6. 本模块接口和对象的权威

[逐字段对象字典](../../api/OBJECTS.md) · [通用约束](../../api/CONVENTIONS.md) · [目录与依赖](../../PROJECT_STRUCTURE.md)

技术表描述实现组件，不新增另一套请求字段。需要签名profile、权限、模型范围等新增字段时先修contracts/策略源，再生成文档和兼容验证。

