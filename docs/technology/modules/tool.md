# Tool：发现、执行与失败治理 · 技术组件设计

技术v0.1 · 2026-10-07 · 主选设计；实际实施范围见[开发记录](../../implementation/README.md)。

[技术总览](../../../TECHNOLOGY_STACK.md) · [模块索引](../README.md) · [框架边界](../FRAMEWORK_BOUNDARIES.md)

## 1. 主选组件与使用阶段

| 组件 | 实际包/服务 | 在本模块承担什么 | 基线与加入时机 |
| --- | --- | --- | --- |
| [Python](https://devguide.python.org/versions/) | `CPython` | 七Runtime和本地Runner语言 | 3.14.x主线；3.13仅兼容回退候选 / 基础 |
| [Pydantic](https://docs.pydantic.dev/latest/concepts/strict_mode/) | `pydantic` | 严格Python DTO与内部类型 | 2.x / 基础 |
| [JSON Schema校验器](https://python-jsonschema.readthedocs.io/en/stable/) | `jsonschema` | 执行现有2020-12契约 | 4.x / Draft202012Validator / 基础 |
| [SQLAlchemy](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html) | `sqlalchemy` | 领域Repository与事务适配 | 2.x异步API / P0 |
| [PostgreSQL](https://www.postgresql.org/support/versioning/) | `数据库服务` | 业务状态、CAS、Outbox与持久待办 | 17.x受支持维护线 / P0 |
| [pgvector](https://github.com/pgvector/pgvector) | `PostgreSQL扩展＋pgvector Python适配` | 工具/资料/记忆向量索引 | 0.8或更高稳定线；冻结匹配PG版本 / P4 |
| [pg_trgm/全文检索](https://www.postgresql.org/docs/17/pgtrgm.html) | `PostgreSQL扩展/内置功能` | 关键词、名称与模糊召回 | 与PostgreSQL主版本一致 / P2/P4 |
| [HTTPX](https://www.python-httpx.org/async/) | `httpx` | 异步联网与连接池 | 稳定版 / P0/P2 |
| [MCP官方Python SDK](https://github.com/modelcontextprotocol/python-sdk) | `mcp` | 批准服务的协议session/能力发现/调用 | 已发布稳定版；协议profile另锁 / P4 |

表中P4/P5或按需组件不要求首轮全部安装。SDK供应商、账户授权、可选环境和格式仍按产品决策/管理员配置确定；组件主选不会扩大权限。

## 2. 接入、细分职责与实现策略

### 注册和检索

ToolSpec与schema在PostgreSQL为权威；注册/更新提交Outbox，索引worker生成带tool版本/embedding profile的pgvector索引。索引滞后不使禁用工具继续可用。

发现依次做角色/flag/当前权限/真实环境过滤、关键词＋向量候选和必要schema加载；当前LLM最终选择。小目录早期直接暴露过滤后候选，P4补向量，能力接口从首轮保留。

pgvector ANN过滤可能减少召回。查询始终包含访问条件；当前规模优先在获准集合精确搜索，规模增大后评测HNSW/iterative_scan和有界扩大候选。禁止跨用户返回未经授权描述或将召回不足解释成能力不存在。

### 一条调用的落地组件

jsonschema规范参数 → 自有PolicyGate → Run审批port → 执行前复核 → SQL持久意图/效果 → provider adapter → ResultNormalizer → 真实回执/审计/结算。

内部agents/context/tasks/workspace等控制工具只转接所属facade。LangGraph ToolBridgeNode调用此入口；任何框架原生Shell/File工具都不能绕过统一闸门。MCP官方SDK仅负责session/协议，工具列表、远端输入输出仍按上述链处理。

### 网络与失败

HTTPX按provider生命周期复用连接池，设置连接/读取/总体截止时间和结果上限；DNS/重定向/实际连接目标与网络政策一起核验，联网进程可用出站代理落实允许范围。字符串URL检查不足以防止重绑定/重定向越界。

重试/退避/熔断用自有FailureController，不叠加HTTP/SDK/框架多层隐藏重试。每次真实attempt入预算。仅登记严格等价契约且授权相容时自动切换提供方，其他替换交当前Agent记录差异；写结果unknown先对账。

MCP HTTP只接批准endpoint，stdio只用批准启动模板和独立受限进程；到期/撤销清理session、候选和缓存，但不把已经发生的外部动作当作已撤销。

## 3. 架构子节点的具体技术落点

| 节点 | 技术组件 | 如何落地 | 策略 / 准确接口 |
| --- | --- | --- | --- |
| `tool` | Python、Pydantic、JSON Schema校验器、PostgreSQL、pgvector、pg_trgm/全文检索 | ToolSpec权威注册，权限过滤与混合索引；LLM最终选择 | [设计](../../design/modules/tool.md) / [接口](../../api/nodes/tool.md) |
| `tool.registry` | Python、Pydantic、JSON Schema校验器、PostgreSQL、pgvector、pg_trgm/全文检索 | ToolSpec权威注册，权限过滤与混合索引；LLM最终选择 | [设计](../../design/components/tool-registry.md) / [接口](../../api/nodes/tool.registry.md) |
| `tool.discovery` | Python、Pydantic、JSON Schema校验器、PostgreSQL、pgvector、pg_trgm/全文检索 | ToolSpec权威注册，权限过滤与混合索引；LLM最终选择 | [设计](../../design/components/tool-discovery.md) / [接口](../../api/nodes/tool.discovery.md) |
| `tool.invocation` | Python、Pydantic、PostgreSQL | 统一InvocationGate调用自有Policy/Run审批/提供方adapter | [设计](../../design/components/tool-invocation.md) / [接口](../../api/nodes/tool.invocation.md) |
| `tool.effects` | Python、Pydantic、SQLAlchemy、PostgreSQL、FSBlobStore | typed回执、真实输出Ref、效果/审计账本与幂等对账 | [设计](../../design/components/tool-effects.md) / [接口](../../api/nodes/tool.effects.md) |
| `tool.failure` | Python、PostgreSQL | 自有attempt/退避/熔断/严格等价恢复控制器 | [设计](../../design/components/tool-failure.md) / [接口](../../api/nodes/tool.failure.md) |
| `tool.mcp` | Python、MCP官方Python SDK、Pydantic、PostgreSQL | 官方SDK session在统一闸门后，连接/能力撤销失效 | [设计](../../design/components/tool-mcp.md) / [接口](../../api/nodes/tool.mcp.md) |
| `tool.adapters` | Python、HTTPX | 批准provider与Runtime control adapters；持久operation边界 | [设计](../../design/components/tool-adapters.md) / [接口](../../api/nodes/tool.adapters.md) |
| `tool.results` | Python、Pydantic、SQLAlchemy、PostgreSQL、FSBlobStore | typed回执、真实输出Ref、效果/审计账本与幂等对账 | [设计](../../design/components/tool-results.md) / [接口](../../api/nodes/tool.results.md) |
| `tool.audit` | Python、Pydantic、SQLAlchemy、PostgreSQL、FSBlobStore | typed回执、真实输出Ref、效果/审计账本与幂等对账 | [设计](../../design/components/tool-audit.md) / [接口](../../api/nodes/tool.audit.md) |
| `tool.invocation.schema` | Python、JSON Schema校验器、Pydantic | 从统一schema验证准确动作分支，拒绝自报信任字段 | [设计](../../design/components/tool-invocation-schema.md) / [接口](../../api/nodes/tool.invocation.schema.md) |
| `tool.invocation.precheck` | Python、Pydantic、PostgreSQL | 统一InvocationGate调用自有Policy/Run审批/提供方adapter | [设计](../../design/components/tool-invocation-precheck.md) / [接口](../../api/nodes/tool.invocation.precheck.md) |
| `tool.invocation.approval` | Python、Pydantic、PostgreSQL | 统一InvocationGate调用自有Policy/Run审批/提供方adapter | [设计](../../design/components/tool-invocation-approval.md) / [接口](../../api/nodes/tool.invocation.approval.md) |
| `tool.invocation.recheck` | Python、Pydantic、PostgreSQL | 统一InvocationGate调用自有Policy/Run审批/提供方adapter | [设计](../../design/components/tool-invocation-recheck.md) / [接口](../../api/nodes/tool.invocation.recheck.md) |
| `tool.invocation.dispatch` | Python、Pydantic、PostgreSQL | 统一InvocationGate调用自有Policy/Run审批/提供方adapter | [设计](../../design/components/tool-invocation-dispatch.md) / [接口](../../api/nodes/tool.invocation.dispatch.md) |
| `tool.invocation.result` | Python、Pydantic、SQLAlchemy、PostgreSQL、FSBlobStore | typed回执、真实输出Ref、效果/审计账本与幂等对账 | [设计](../../design/components/tool-invocation-result.md) / [接口](../../api/nodes/tool.invocation.result.md) |
| `tool.mcp.provider` | Python、MCP官方Python SDK、Pydantic、PostgreSQL | 官方SDK session在统一闸门后，连接/能力撤销失效 | [设计](../../design/components/tool-mcp-provider.md) / [接口](../../api/nodes/tool.mcp.provider.md) |
| `tool.mcp.session` | Python、MCP官方Python SDK、Pydantic、PostgreSQL | 官方SDK session在统一闸门后，连接/能力撤销失效 | [设计](../../design/components/tool-mcp-session.md) / [接口](../../api/nodes/tool.mcp.session.md) |
| `tool.mcp.capabilities` | Python、MCP官方Python SDK、Pydantic、PostgreSQL | 官方SDK session在统一闸门后，连接/能力撤销失效 | [设计](../../design/components/tool-mcp-capabilities.md) / [接口](../../api/nodes/tool.mcp.capabilities.md) |
| `tool.mcp.invoke` | Python、MCP官方Python SDK、Pydantic、PostgreSQL | 官方SDK session在统一闸门后，连接/能力撤销失效 | [设计](../../design/components/tool-mcp-invoke.md) / [接口](../../api/nodes/tool.mcp.invoke.md) |
| `tool.mcp.invalidate` | Python、MCP官方Python SDK、Pydantic、PostgreSQL | 官方SDK session在统一闸门后，连接/能力撤销失效 | [设计](../../design/components/tool-mcp-invalidate.md) / [接口](../../api/nodes/tool.mcp.invalidate.md) |

## 4. 目录与依赖位置

- `src/uaw/tool/`
- `src/uaw/tool/control/`
- `src/uaw/tool/providers/`

目录为完整开发目标，部分工程设施已实现，业务能力以实际记录为准。领域contracts/ports保留UAW类型；第三方库在实现adapter中使用，composition负责组装。框架或ORM对象不能成为跨Runtime公开协议。

## 5. 对应开发轮次与验收

| 工作包 | 本轮职责 | 当前状态 |
| --- | --- | --- |
| [P1-03 工具目录与完整调用闸门](../../plan/rounds/P1-03.md) | 使模型提出的动作经过参数、权限、审批和真实结果处理。 | planned |
| [P2-02 联网搜索与网页读取](../../plan/rounds/P2-02.md) | 通过管理员提供方获取可核验外部资料。 | planned |
| [P3-03 独立工具并发与回压](../../plan/rounds/P3-03.md) | 只并发可证明独立的动作，并保持账本正确。 | planned |
| [P4-03 角色过滤与向量混合发现](../../plan/rounds/P4-03.md) | 扩大工具目录而保留LLM最终选择。 | planned |
| [P4-05 MCP与私人账号连接生命周期](../../plan/rounds/P4-05.md) | 可安装接入能力，但授权由真实账户和政策决定。 | planned |
| [P5-02 租约、当前权限与安全续跑](../../plan/rounds/P5-02.md) | 恢复未完工作而不重复未知外部写。 | planned |

关联轮次覆盖主责与协同工作，不等于每轮都实现本模块全部功能。按轮任务/具体能力附真实证据，再核对 [技术兼容与接入验证](../VALIDATION.md)。

## 6. 本模块接口和对象的权威

[逐字段对象字典](../../api/OBJECTS.md) · [通用约束](../../api/CONVENTIONS.md) · [目录与依赖](../../PROJECT_STRUCTURE.md)

技术表描述实现组件，不新增另一套请求字段。需要签名profile、权限、模型范围等新增字段时先修contracts/策略源，再生成文档和兼容验证。

