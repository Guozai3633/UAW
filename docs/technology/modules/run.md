# Run：历史、审批与恢复 · 技术组件设计

技术v0.1 · 2026-10-07 · 主选设计；实际实施范围见[开发记录](../../implementation/README.md)。

[技术总览](../../../TECHNOLOGY_STACK.md) · [模块索引](../README.md) · [框架边界](../FRAMEWORK_BOUNDARIES.md)

## 1. 主选组件与使用阶段

| 组件 | 实际包/服务 | 在本模块承担什么 | 基线与加入时机 |
| --- | --- | --- | --- |
| [Python](https://devguide.python.org/versions/) | `CPython` | 七Runtime和本地Runner语言 | 3.14.x主线；3.13仅兼容回退候选 / 基础 |
| [Pydantic](https://docs.pydantic.dev/latest/concepts/strict_mode/) | `pydantic` | 严格Python DTO与内部类型 | 2.x / 基础 |
| [JSON Schema校验器](https://python-jsonschema.readthedocs.io/en/stable/) | `jsonschema` | 执行现有2020-12契约 | 4.x / Draft202012Validator / 基础 |
| [SQLAlchemy](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html) | `sqlalchemy` | 领域Repository与事务适配 | 2.x异步API / P0 |
| [Psycopg](https://www.psycopg.org/psycopg3/docs/) | `psycopg` | PostgreSQL异步驱动 | 3.x稳定发行版 / P0 |
| [PostgreSQL](https://www.postgresql.org/support/versioning/) | `数据库服务` | 业务状态、CAS、Outbox与持久待办 | 17.x受支持维护线 / P0 |
| [LangGraph PostgreSQL Checkpointer](https://docs.langchain.com/oss/python/langgraph/persistence) | `langgraph-checkpoint-postgres` | 图执行位置；由Run恢复门控制 | 与langgraph成组锁定 / P1局部保存；P5复合恢复 |
| [structlog](https://www.structlog.org/en/stable/) | `structlog` | 结构化脱敏日志 | 稳定版 / P0，P5完善 |

表中P4/P5或按需组件不要求首轮全部安装。SDK供应商、账户授权、可选环境和格式仍按产品决策/管理员配置确定；组件主选不会扩大权限。

## 2. 接入、细分职责与实现策略

### 权威状态与事件

Conversation/InputRecord/Run、InteractionItem、审批、预算、取消、Checkpoint等按本领域SQL仓储保存。每个领域更新带CAS，事件与Outbox在同一事务提交，seq在Run内单调且唯一。错误或未提交内容不能先广播成功。

API受理后让Run/Outbox持久记录待执行；自有worker用PostgreSQL短事务claim和有界并发执行。LISTEN/NOTIFY只用作唤醒提示，丢提示也能扫描未处理记录。首版不要求Celery、Kafka或Redis队列。

领取消息不等于持有长任务执行权。实际提交重查ExecutionLease/fencing和领域revision；过期worker即使仍在运行也不能提交。外部派发走Tool/Runner幂等与对账，不能承诺消息只投递一次就解决副作用。

### 审批和用户干预

审批请求/参数Hash/资源/有效期/政策revision由UAW保存，LangGraph interrupt只暂停局部图。用户manual决定经验证才持久化，恢复图前再次核对当前批准。assisted/automatic语义仍待D07，模型代审通过ModelGateway且不拥有执行权。

steer/enqueue/replace/cancel/deliver_partial持久化不同控制意图；仅在安全边界执行。目标改变使关联Frame/Plan/结果失效，不抹去已有效果。

### 复合检查点和恢复

LangGraph checkpointer可写同一个PostgreSQL实例的独立表，但不拥有Task/Workspace/权限状态。先取得已完成图保存回执及领域已提交版本，再发布RunCheckpoint引用和事件水位；半写入状态不能发布成可恢复检查点。

恢复先核验租约、兼容版本、当前授权、未知效果和真实工作区，再由EngineAdapter载入局部图。没有跨全部模块的巨型事务承诺；不一致引用被阻断或从最后已发布边界重建。事件回放和新Run重跑使用独立入口。

定时使用持久TriggerSpec、时区和occurrence去重，自有扫描worker创建Run；节点Scheduler不会兼任任务触发器。P5-04实现后仍默认关闭。

## 3. 架构子节点的具体技术落点

| 节点 | 技术组件 | 如何落地 | 策略 / 准确接口 |
| --- | --- | --- | --- |
| `run` | Python、Pydantic、SQLAlchemy、PostgreSQL | Run领域权威、事务Outbox、SQL待办、审批和控制意图 | [设计](../../design/modules/run.md) / [接口](../../api/nodes/run.md) |
| `run.history` | Python、Pydantic、SQLAlchemy、PostgreSQL | Run领域权威、事务Outbox、SQL待办、审批和控制意图 | [设计](../../design/components/run-history.md) / [接口](../../api/nodes/run.history.md) |
| `run.state` | Python、Pydantic、SQLAlchemy、PostgreSQL | Run领域权威、事务Outbox、SQL待办、审批和控制意图 | [设计](../../design/components/run-state.md) / [接口](../../api/nodes/run.state.md) |
| `run.events` | Python、Pydantic、SQLAlchemy、PostgreSQL | Run领域权威、事务Outbox、SQL待办、审批和控制意图 | [设计](../../design/components/run-events.md) / [接口](../../api/nodes/run.events.md) |
| `run.budget` | Python、Pydantic、SQLAlchemy、PostgreSQL | Run领域权威、事务Outbox、SQL待办、审批和控制意图 | [设计](../../design/components/run-budget.md) / [接口](../../api/nodes/run.budget.md) |
| `run.approval` | Python、Pydantic、SQLAlchemy、PostgreSQL | Run领域权威、事务Outbox、SQL待办、审批和控制意图 | [设计](../../design/components/run-approval.md) / [接口](../../api/nodes/run.approval.md) |
| `run.checkpoint` | Python、PostgreSQL、LangGraph PostgreSQL Checkpointer | 已保存图位置＋已提交领域Ref组成发布检查点 | [设计](../../design/components/run-checkpoint.md) / [接口](../../api/nodes/run.checkpoint.md) |
| `run.resume` | Python、Pydantic、PostgreSQL、LangGraph PostgreSQL Checkpointer | 先租约/当前授权/效果与工作区核验，再恢复Engine | [设计](../../design/components/run-resume.md) / [接口](../../api/nodes/run.resume.md) |
| `run.cancel` | Python、Pydantic、SQLAlchemy、PostgreSQL | Run领域权威、事务Outbox、SQL待办、审批和控制意图 | [设计](../../design/components/run-cancel.md) / [接口](../../api/nodes/run.cancel.md) |
| `run.trigger` | Python、Pydantic、SQLAlchemy、PostgreSQL | Run领域权威、事务Outbox、SQL待办、审批和控制意图 | [设计](../../design/components/run-trigger.md) / [接口](../../api/nodes/run.trigger.md) |
| `run.resume.lease` | Python、Pydantic、PostgreSQL、LangGraph PostgreSQL Checkpointer | 先租约/当前授权/效果与工作区核验，再恢复Engine | [设计](../../design/components/run-resume-lease.md) / [接口](../../api/nodes/run.resume.lease.md) |
| `run.resume.versions` | Python、Pydantic、PostgreSQL、LangGraph PostgreSQL Checkpointer | 先租约/当前授权/效果与工作区核验，再恢复Engine | [设计](../../design/components/run-resume-versions.md) / [接口](../../api/nodes/run.resume.versions.md) |
| `run.resume.access` | Python、Pydantic、PostgreSQL、LangGraph PostgreSQL Checkpointer | 先租约/当前授权/效果与工作区核验，再恢复Engine | [设计](../../design/components/run-resume-access.md) / [接口](../../api/nodes/run.resume.access.md) |
| `run.resume.effects` | Python、Pydantic、PostgreSQL、LangGraph PostgreSQL Checkpointer | 先租约/当前授权/效果与工作区核验，再恢复Engine | [设计](../../design/components/run-resume-effects.md) / [接口](../../api/nodes/run.resume.effects.md) |
| `run.resume.workspace` | Python、Pydantic、PostgreSQL、LangGraph PostgreSQL Checkpointer | 先租约/当前授权/效果与工作区核验，再恢复Engine | [设计](../../design/components/run-resume-workspace.md) / [接口](../../api/nodes/run.resume.workspace.md) |
| `run.resume.continue` | Python、Pydantic、PostgreSQL、LangGraph PostgreSQL Checkpointer | 先租约/当前授权/效果与工作区核验，再恢复Engine | [设计](../../design/components/run-resume-continue.md) / [接口](../../api/nodes/run.resume.continue.md) |

## 4. 目录与依赖位置

- `src/uaw/run/`
- `src/uaw/run/resume/`
- `src/uaw/infrastructure/db/`

目录为完整开发目标，部分工程设施已实现，业务能力以实际记录为准。领域contracts/ports保留UAW类型；第三方库在实现adapter中使用，composition负责组装。框架或ORM对象不能成为跨Runtime公开协议。

## 5. 对应开发轮次与验收

| 工作包 | 本轮职责 | 当前状态 |
| --- | --- | --- |
| [P0-04 受理、原文、状态、事件与资源账本](../../plan/rounds/P0-04.md) | 保存原文并以真实状态和用量驱动后续执行。 | accepted |
| [P1-09 人工审批、基础干预与取消](../../plan/rounds/P1-09.md) | 用户可停止或修正当前单Agent任务。 | planned |
| [P3-03 独立工具并发与回压](../../plan/rounds/P3-03.md) | 只并发可证明独立的动作，并保持账本正确。 | planned |
| [P3-07 复杂运行干预与多会话任务](../../plan/rounds/P3-07.md) | 处理目标修订、排队、部分交付和同用户共享任务。 | planned |
| [P4-09 草稿提示、用户控制与完整管理页面](../../plan/rounds/P4-09.md) | 完成实际能力的可理解交互，区分用户和管理员。 | planned |
| [P5-01 跨域检查点与一致提交边界](../../plan/rounds/P5-01.md) | 保存可核验的续跑位置和未决动作。 | planned |
| [P5-02 租约、当前权限与安全续跑](../../plan/rounds/P5-02.md) | 恢复未完工作而不重复未知外部写。 | planned |
| [P5-04 handoff与定时扩展实现](../../plan/rounds/P5-04.md) | 完善已规划扩展，但独立UAW首个试用默认关闭。 | planned |

关联轮次覆盖主责与协同工作，不等于每轮都实现本模块全部功能。按轮任务/具体能力附真实证据，再核对 [技术兼容与接入验证](../VALIDATION.md)。

## 6. 本模块接口和对象的权威

[逐字段对象字典](../../api/OBJECTS.md) · [通用约束](../../api/CONVENTIONS.md) · [目录与依赖](../../PROJECT_STRUCTURE.md)

技术表描述实现组件，不新增另一套请求字段。需要签名profile、权限、模型范围等新增字段时先修contracts/策略源，再生成文档和兼容验证。

