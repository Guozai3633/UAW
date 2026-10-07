# Agent：主循环、角色与协作 · 技术组件设计

技术v0.1 · 2026-10-07 · 主选设计；实际实施范围见[开发记录](../../implementation/README.md)。

[技术总览](../../../TECHNOLOGY_STACK.md) · [模块索引](../README.md) · [框架边界](../FRAMEWORK_BOUNDARIES.md)

## 1. 主选组件与使用阶段

| 组件 | 实际包/服务 | 在本模块承担什么 | 基线与加入时机 |
| --- | --- | --- | --- |
| [Python](https://devguide.python.org/versions/) | `CPython` | 七Runtime和本地Runner语言 | 3.14.x主线；3.13仅兼容回退候选 / 基础 |
| [Pydantic](https://docs.pydantic.dev/latest/concepts/strict_mode/) | `pydantic` | 严格Python DTO与内部类型 | 2.x / 基础 |
| [JSON Schema校验器](https://python-jsonschema.readthedocs.io/en/stable/) | `jsonschema` | 执行现有2020-12契约 | 4.x / Draft202012Validator / 基础 |
| [LangGraph](https://docs.langchain.com/oss/python/langgraph/overview) | `langgraph` | 单个Agent实例内部循环的执行后端 | 稳定发行版；不使用main/dev / P1，需边界验证 |
| [LangGraph PostgreSQL Checkpointer](https://docs.langchain.com/oss/python/langgraph/persistence) | `langgraph-checkpoint-postgres` | 图执行位置；由Run恢复门控制 | 与langgraph成组锁定 / P1局部保存；P5复合恢复 |
| [SQLAlchemy](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html) | `sqlalchemy` | 领域Repository与事务适配 | 2.x异步API / P0 |
| [PostgreSQL](https://www.postgresql.org/support/versioning/) | `数据库服务` | 业务状态、CAS、Outbox与持久待办 | 17.x受支持维护线 / P0 |
| [pgvector](https://github.com/pgvector/pgvector) | `PostgreSQL扩展＋pgvector Python适配` | 工具/资料/记忆向量索引 | 0.8或更高稳定线；冻结匹配PG版本 / P4 |
| [pg_trgm/全文检索](https://www.postgresql.org/docs/17/pgtrgm.html) | `PostgreSQL扩展/内置功能` | 关键词、名称与模糊召回 | 与PostgreSQL主版本一致 / P2/P4 |

表中P4/P5或按需组件不要求首轮全部安装。SDK供应商、账户授权、可选环境和格式仍按产品决策/管理员配置确定；组件主选不会扩大权限。

## 2. 接入、细分职责与实现策略

### LangGraph负责到哪一层

主选StateGraph实现**单个Agent实例内部循环**：build_context → model_action → 条件分派 → tool/delegate/wait/verify → 下一步。各节点调用UAW port，LLM可以动态选择动作。七Runtime职责图不编译成每次必经的七步链。

`loop.py`依赖自有AgentEnginePort；`engines/langgraph.py`封装框架，`engines/asyncio_engine.py`是兼容回退候选，只有实际实现并验收后才能启用。首版只做主选引擎，避免同时维护两套完整行为。

### 定义、实例和调用

- Definitions：主Agent加载精炼设计方法，经agents.create/update保存会话定义。Pydantic/jsonschema检查职责/模型意图/预算/权限；SQL存不可变版本。create不创建运行图。
- Factory：agents.invoke经授权校验后才创建实例、预算份额、隔离上下文和Engine实例。用户固定模型默认继承，显式子模型必须有真实用户依据。
- Namespace：持久图标识绑定workspace/run/agent实例和执行纪元；不能只用conversation_id，让父子图或两轮Run共用执行位置。
- Skills：自有SkillLoader读批准能力包中的方法、脚本、模板和验收规范，按需加载；能力包与定义分别版本化。办公/学术通过技能和角色扩展。
- Completion：要求/证据/语义/版本/交付/用户接受六层仍由自有控制器落实，不以LangGraph到END当作任务成功。

### Planning、调度和协作

LLM输出none/steps/dag与委派/并发提案，jsonschema检查互斥分支。自有Planner校验并CAS提交计划；`graphlib.TopologicalSorter`可作无环/拓扑辅助，但动态修订后重建当前就绪集。

Scheduler管理TaskGraph依赖、资源、写集合和版本失效；asyncio TaskGroup/Semaphore执行获准并行工作。LangGraph只执行每个Agent局部循环。工具并发调用经过同一个ToolRuntime，多个子Agent分别拥有实例与图。

Board、Join和父子Channel以SQL版本化记录和Ref共享，不广播全量父prompt或可写Python对象。Join重查当前依赖并交父汇总；子成功不自动使父成功。取消由Run持久标记传播，等待实际执行回执。

### 检查点与副作用

P1使用LangGraph PostgreSQL checkpointer保存局部执行位置，因为interrupt等待本身需要checkpointer；实例thread_id与当前批准由UAW绑定，节点重入复用已持久化operation_id。P5才发布持有图检查点及领域版本的复合RunCheckpoint，补齐进程重启后的安全恢复。P1服务重启的未完任务保持待核验，不让框架从旧图直接续跑。

图状态只保存批准的JSON原语/Ref/版本；工具客户端、凭据、任意对象和Pickle不得持久化。审批状态以Run仓储为准，框架interrupt仅作为等待机制。

## 3. 架构子节点的具体技术落点

| 节点 | 技术组件 | 如何落地 | 策略 / 准确接口 |
| --- | --- | --- | --- |
| `agent` | Python、Pydantic、LangGraph、PostgreSQL | 自有AgentRuntime，EnginePort封装局部循环 | [设计](../../design/modules/agent.md) / [接口](../../api/nodes/agent.md) |
| `agent.definitions` | Python、Pydantic、JSON Schema校验器、SQLAlchemy、PostgreSQL | create/update/diff/revert是会话定义服务，定义不等于实例 | [设计](../../design/components/agent-definitions.md) / [接口](../../api/nodes/agent.definitions.md) |
| `agent.loop` | Python、LangGraph | StateGraph调用UAW ports，动作条件由LLM选择 | [设计](../../design/components/agent-loop.md) / [接口](../../api/nodes/agent.loop.md) |
| `agent.assessment` | Python、Pydantic、JSON Schema校验器 | 当前继承模型语义提案＋自有范围/来源校验 | [设计](../../design/components/agent-assessment.md) / [接口](../../api/nodes/agent.assessment.md) |
| `agent.planning` | Python、Pydantic、PostgreSQL | 自有版本化Plan、graphlib无环辅助、asyncio有界调度 | [设计](../../design/components/agent-planning.md) / [接口](../../api/nodes/agent.planning.md) |
| `agent.scheduler` | Python、Pydantic、PostgreSQL | 自有版本化Plan、graphlib无环辅助、asyncio有界调度 | [设计](../../design/components/agent-scheduler.md) / [接口](../../api/nodes/agent.scheduler.md) |
| `agent.collaboration` | Python、Pydantic、PostgreSQL、LangGraph | 有界实例工厂/权限预算交集；每实例独立Engine和图命名空间 | [设计](../../design/components/agent-collaboration.md) / [接口](../../api/nodes/agent.collaboration.md) |
| `agent.skills` | Python、Pydantic、JSON Schema校验器 | 自有批准SkillLoader/Manifest，按需加载方法与模板 | [设计](../../design/components/agent-skills.md) / [接口](../../api/nodes/agent.skills.md) |
| `agent.completion` | Python、Pydantic、JSON Schema校验器、SQLAlchemy、PostgreSQL | 自有完成控制器核验实际Ref/版本，用户接受独立记录 | [设计](../../design/components/agent-completion.md) / [接口](../../api/nodes/agent.completion.md) |
| `agent.board` | Python、Pydantic、SQLAlchemy、PostgreSQL | 版本Ref/共享板/CAS控制租约，Run取消传播，父汇总验收 | [设计](../../design/components/agent-board.md) / [接口](../../api/nodes/agent.board.md) |
| `agent.factory` | Python、Pydantic、PostgreSQL、LangGraph | 有界实例工厂/权限预算交集；每实例独立Engine和图命名空间 | [设计](../../design/components/agent-factory.md) / [接口](../../api/nodes/agent.factory.md) |
| `agent.definitions.designer` | Python、Pydantic、JSON Schema校验器 | 当前继承模型语义提案＋自有范围/来源校验 | [设计](../../design/components/agent-definitions-designer.md) / [接口](../../api/nodes/agent.definitions.designer.md) |
| `agent.definitions.validator` | Python、Pydantic、JSON Schema校验器、SQLAlchemy、PostgreSQL | create/update/diff/revert是会话定义服务，定义不等于实例 | [设计](../../design/components/agent-definitions-validator.md) / [接口](../../api/nodes/agent.definitions.validator.md) |
| `agent.definitions.model_intent` | Python、Pydantic、JSON Schema校验器 | 当前继承模型语义提案＋自有范围/来源校验 | [设计](../../design/components/agent-definitions-model_intent.md) / [接口](../../api/nodes/agent.definitions.model_intent.md) |
| `agent.definitions.repository` | Python、Pydantic、JSON Schema校验器、SQLAlchemy、PostgreSQL | create/update/diff/revert是会话定义服务，定义不等于实例 | [设计](../../design/components/agent-definitions-repository.md) / [接口](../../api/nodes/agent.definitions.repository.md) |
| `agent.definitions.discovery` | Python、PostgreSQL、pgvector、pg_trgm/全文检索 | 会话内候选摘要发现，向量按P4加入，LLM选择invoke | [设计](../../design/components/agent-definitions-discovery.md) / [接口](../../api/nodes/agent.definitions.discovery.md) |
| `agent.definitions.change_service` | Python、Pydantic、JSON Schema校验器、SQLAlchemy、PostgreSQL | create/update/diff/revert是会话定义服务，定义不等于实例 | [设计](../../design/components/agent-definitions-change_service.md) / [接口](../../api/nodes/agent.definitions.change_service.md) |
| `agent.collaboration.contract` | Python、Pydantic、PostgreSQL、LangGraph | 有界实例工厂/权限预算交集；每实例独立Engine和图命名空间 | [设计](../../design/components/agent-collaboration-contract.md) / [接口](../../api/nodes/agent.collaboration.contract.md) |
| `agent.collaboration.instance` | Python、Pydantic、PostgreSQL、LangGraph | 有界实例工厂/权限预算交集；每实例独立Engine和图命名空间 | [设计](../../design/components/agent-collaboration-instance.md) / [接口](../../api/nodes/agent.collaboration.instance.md) |
| `agent.collaboration.channel` | Python、Pydantic、SQLAlchemy、PostgreSQL | 版本Ref/共享板/CAS控制租约，Run取消传播，父汇总验收 | [设计](../../design/components/agent-collaboration-channel.md) / [接口](../../api/nodes/agent.collaboration.channel.md) |
| `agent.collaboration.join` | Python、Pydantic、SQLAlchemy、PostgreSQL | 版本Ref/共享板/CAS控制租约，Run取消传播，父汇总验收 | [设计](../../design/components/agent-collaboration-join.md) / [接口](../../api/nodes/agent.collaboration.join.md) |
| `agent.collaboration.handoff` | Python、Pydantic、SQLAlchemy、PostgreSQL | 版本Ref/共享板/CAS控制租约，Run取消传播，父汇总验收 | [设计](../../design/components/agent-collaboration-handoff.md) / [接口](../../api/nodes/agent.collaboration.handoff.md) |
| `agent.collaboration.cancel` | Python、Pydantic、SQLAlchemy、PostgreSQL | 版本Ref/共享板/CAS控制租约，Run取消传播，父汇总验收 | [设计](../../design/components/agent-collaboration-cancel.md) / [接口](../../api/nodes/agent.collaboration.cancel.md) |
| `agent.completion.contract` | Python、Pydantic、JSON Schema校验器、SQLAlchemy、PostgreSQL | 自有完成控制器核验实际Ref/版本，用户接受独立记录 | [设计](../../design/components/agent-completion-contract.md) / [接口](../../api/nodes/agent.completion.contract.md) |
| `agent.completion.evidence` | Python、Pydantic、JSON Schema校验器、SQLAlchemy、PostgreSQL | 自有完成控制器核验实际Ref/版本，用户接受独立记录 | [设计](../../design/components/agent-completion-evidence.md) / [接口](../../api/nodes/agent.completion.evidence.md) |
| `agent.completion.semantic` | Python、Pydantic、JSON Schema校验器 | 当前继承模型语义提案＋自有范围/来源校验 | [设计](../../design/components/agent-completion-semantic.md) / [接口](../../api/nodes/agent.completion.semantic.md) |
| `agent.completion.version` | Python、Pydantic、JSON Schema校验器、SQLAlchemy、PostgreSQL | 自有完成控制器核验实际Ref/版本，用户接受独立记录 | [设计](../../design/components/agent-completion-version.md) / [接口](../../api/nodes/agent.completion.version.md) |
| `agent.completion.delivery` | Python、Pydantic、JSON Schema校验器、SQLAlchemy、PostgreSQL | 自有完成控制器核验实际Ref/版本，用户接受独立记录 | [设计](../../design/components/agent-completion-delivery.md) / [接口](../../api/nodes/agent.completion.delivery.md) |
| `agent.completion.acceptance` | Python、Pydantic、JSON Schema校验器、SQLAlchemy、PostgreSQL | 自有完成控制器核验实际Ref/版本，用户接受独立记录 | [设计](../../design/components/agent-completion-acceptance.md) / [接口](../../api/nodes/agent.completion.acceptance.md) |

## 4. 目录与依赖位置

- `src/uaw/agent/`
- `src/uaw/agent/engines/`
- `src/uaw/tool/control/`
- `capabilities/builtin/`

目录为完整开发目标，部分工程设施已实现，业务能力以实际记录为准。领域contracts/ports保留UAW类型；第三方库在实现adapter中使用，composition负责组装。框架或ORM对象不能成为跨Runtime公开协议。

## 5. 对应开发轮次与验收

| 工作包 | 本轮职责 | 当前状态 |
| --- | --- | --- |
| [P1-07 根实例、单Agent循环与工具接线](../../plan/rounds/P1-07.md) | 由主Agent动态决定下一步并完成实际工作。 | planned |
| [P1-08 交付契约、证据和完成提交](../../plan/rounds/P1-08.md) | 以真实要求、实际检查和版本决定是否完成。 | planned |
| [P2-03 技能加载与可复用任务模板](../../plan/rounds/P2-03.md) | 让操作方法按需复用而不靠长主提示词。 | planned |
| [P2-04 会话子Agent定义的设计和版本管理](../../plan/rounds/P2-04.md) | 用户可用自然语言创建、修改和撤销角色。 | planned |
| [P2-05 首次有界子Agent调用](../../plan/rounds/P2-05.md) | 把定义转换为独立上下文和受限执行实例。 | planned |
| [P2-06 共享结果板与Join](../../plan/rounds/P2-06.md) | 父Agent可靠收集结果并保留最终交付责任。 | planned |
| [P2-07 办公与学术方法和成果验收](../../plan/rounds/P2-07.md) | 在通用架构上实现两个可复用工作场景。 | planned |
| [P3-01 语义执行评估与步骤计划](../../plan/rounds/P3-01.md) | 独立判断规划、委派、并发和信息缺口。 | planned |
| [P3-02 DAG验证与有界调度](../../plan/rounds/P3-02.md) | 以真实依赖和资源执行任务图。 | planned |
| [P3-04 多个子Agent并行与树级约束](../../plan/rounds/P3-04.md) | 运行多个独立分工并控制父子深度、预算和取消。 | planned |
| [P3-06 块级审阅、局部应用与撤销](../../plan/rounds/P3-06.md) | 用户能选择具体改动和反馈位置。 | planned |
| [P3-07 复杂运行干预与多会话任务](../../plan/rounds/P3-07.md) | 处理目标修订、排队、部分交付和同用户共享任务。 | planned |
| [P4-03 角色过滤与向量混合发现](../../plan/rounds/P4-03.md) | 扩大工具目录而保留LLM最终选择。 | planned |
| [P4-08 明确Auto授权与能力恢复](../../plan/rounds/P4-08.md) | 固定模型仍不变，Auto只能在用户授权范围内选择。 | planned |
| [P5-04 handoff与定时扩展实现](../../plan/rounds/P5-04.md) | 完善已规划扩展，但独立UAW首个试用默认关闭。 | planned |

关联轮次覆盖主责与协同工作，不等于每轮都实现本模块全部功能。按轮任务/具体能力附真实证据，再核对 [技术兼容与接入验证](../VALIDATION.md)。

## 6. 本模块接口和对象的权威

[逐字段对象字典](../../api/OBJECTS.md) · [通用约束](../../api/CONVENTIONS.md) · [目录与依赖](../../PROJECT_STRUCTURE.md)

技术表描述实现组件，不新增另一套请求字段。需要签名profile、权限、模型范围等新增字段时先修contracts/策略源，再生成文档和兼容验证。

