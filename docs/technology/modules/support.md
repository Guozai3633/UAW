# 共享设施：存储、缓存、配置与观测 · 技术组件设计

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
| [Alembic](https://alembic.sqlalchemy.org/en/latest/) | `alembic` | 人工审阅的数据库迁移 | 稳定版/SQLAlchemy 2 / P0 |
| [PostgreSQL](https://www.postgresql.org/support/versioning/) | `数据库服务` | 业务状态、CAS、Outbox与持久待办 | 17.x受支持维护线 / P0 |
| FSBlobStore | `UAW自有Python适配器` | 私有数据卷中的不可变大内容 | BlobStorePort v0.1 / P0 |
| [S3 Blob适配](https://docs.aws.amazon.com/boto3/latest/reference/services/s3.html) | `boto3` | 后续对象存储后端 | 稳定版＋提供方能力验证 / 按需 |
| [cachetools](https://cachetools.readthedocs.io/en/stable/) | `cachetools` | 有界进程缓存；锁和失效由UAW管理 | 稳定版 / P4 |
| [OS凭据库](https://keyring.readthedocs.io/en/latest/) | `keyring` | 设备私钥及本机秘密存取 | 稳定版/批准OS backend / P1 |
| [cryptography/Ed25519](https://cryptography.io/en/latest/hazmat/primitives/asymmetric/ed25519/) | `cryptography` | Runner信封/回执签名 | 稳定版，明确签名profile / P1 |
| [structlog](https://www.structlog.org/en/stable/) | `structlog` | 结构化脱敏日志 | 稳定版 / P0，P5完善 |
| [OpenTelemetry](https://opentelemetry.io/docs/languages/python/) | `opentelemetry-api/sdk及OTLP exporter` | 跨模块trace和指标接口 | 兼容稳定组合 / P5 |
| [pytest](https://docs.pytest.org/en/stable/) | `pytest/pytest-asyncio` | 状态/权限/恢复和真实场景检查 | 稳定兼容组合 / P0起 |

表中P4/P5或按需组件不要求首轮全部安装。SDK供应商、账户授权、可选环境和格式仍按产品决策/管理员配置确定；组件主选不会扩大权限。

## 2. 接入、细分职责与实现策略

### 持久化与配置

SQLAlchemy AsyncSession每个工作单元独立，不在并发Agent之间共享一个Session。Psycopg异步连接池按API/worker进程配置，Alembic迁移由发布步骤执行一次，禁止每个请求或worker自动改表。

业务事实在领域Repository，基础设施只实现UnitOfWork/连接/Blob/Index，不产生第八个万能Runtime。必要索引、主体条件、外键、CAS和幂等唯一约束落实到数据库。接口DTO不等于数据库实体。

配置草案校验后激活不可变修订；运行固定内容版本，撤销仍按当前安全政策生效。秘密通过CredentialStorePort取用。开发可用受保护外部配置，Runner用批准OS keyring；部署Secret Manager供应商待环境决定，不把数据库密文字段和解密主密钥放在一起。

### Blob与缓存

首个Blob适配为应用私有持久卷FSBlobStore，元数据/访问范围/保留政策在SQL。S3兼容backend作为后续主选adapter，实际语义需提供方验收。blob先持久化再提交引用，孤儿按保留规则回收，不能借内容Hash跨用户暴露数据。

cachetools仅作为有界L1容器；UAW实现Manifest key、当前访问复核、依赖epoch、容量/字节预算和single-flight。多线程访问有锁，async任务等待和取消单独控制。可持久派生结果用SQL+Blob，首版没有分布式缓存必需项。

语义压缩/结果复用/provider前缀命中分别统计。审批、当前进程状态、未知写、操作幂等不靠结果缓存；能力撤销/记忆删除阻断旧派生内容。跨worker规模出现后再引入分布式缓存adapter并验证收益。

### 能力包、观测与评测

Skill/Tool/Role能力包用自有Manifest、Hash、来源、依赖和旗标管理，安装不自动授予账户或主机权限；归档路径、脚本启动模板和升级回滚都校验。

structlog输出默认仅ID、版本、状态、用量和受控摘要；OpenTelemetry连接跨模块trace，源资料/prompt/秘密不自动导出。LangSmith可后续接adapter，需明确数据导出授权，不成为核心依赖。

pytest场景、版本化材料和人工/语义grader组成评测；模型评审继承既有政策。接受率、返工与全部尝试成本用于发布判断，接口/文档数量不是质量指标。

## 3. 架构子节点的具体技术落点

| 节点 | 技术组件 | 如何落地 | 策略 / 准确接口 |
| --- | --- | --- | --- |
| `support` | Python、Pydantic | 独立共享ports和控制层入口，不增加万能Runtime | [设计](../../design/modules/support.md) / [接口](../../api/nodes/support.md) |
| `support.configuration` | Python、Pydantic、JSON Schema校验器、PostgreSQL、OS凭据库、cryptography/Ed25519 | 配置修订/激活/撤销和CredentialStore，部署秘密backend独立 | [设计](../../design/components/support-configuration.md) / [接口](../../api/nodes/support.configuration.md) |
| `support.extensions` | Python、Pydantic、JSON Schema校验器、PostgreSQL | 自有能力Manifest/来源/Hash/依赖/回滚；安装不授予权限 | [设计](../../design/components/support-extensions.md) / [接口](../../api/nodes/support.extensions.md) |
| `support.cache` | Python、cachetools、PostgreSQL、FSBlobStore | L1＋可持久派生结果，依赖epoch和single-flight由UAW实现 | [设计](../../design/components/support-cache.md) / [接口](../../api/nodes/support.cache.md) |
| `support.observability` | Python、structlog、OpenTelemetry | 脱敏关联日志与版本/attempt trace，默认不导出内容 | [设计](../../design/components/support-observability.md) / [接口](../../api/nodes/support.observability.md) |
| `support.evaluation` | Python、pytest、PostgreSQL | 版本场景、真实回执、人工/语义grader与发布阈值 | [设计](../../design/components/support-evaluation.md) / [接口](../../api/nodes/support.evaluation.md) |
| `support.stores` | Python、SQLAlchemy、Psycopg、Alembic、PostgreSQL、FSBlobStore、S3 Blob适配 | 领域Repository适配、迁移、事务、Blob/Index ports | [设计](../../design/components/support-stores.md) / [接口](../../api/nodes/support.stores.md) |

## 4. 目录与依赖位置

- `src/uaw/shared/`
- `src/uaw/infrastructure/`
- `capabilities/`
- `ops/`

目录为完整开发目标，部分工程设施已实现，业务能力以实际记录为准。领域contracts/ports保留UAW类型；第三方库在实现adapter中使用，composition负责组装。框架或ORM对象不能成为跨Runtime公开协议。

## 5. 对应开发轮次与验收

| 工作包 | 本轮职责 | 当前状态 |
| --- | --- | --- |
| [P0-01 工程启动与最小契约](../../plan/rounds/P0-01.md) | 建立能启动的Python应用和依赖组装，避免先实现全部未来DTO。 | accepted |
| [P0-02 持久化、CAS、blob与事件提交边界](../../plan/rounds/P0-02.md) | 让受理/版本冲突和大内容存取有唯一权威。 | in_progress |
| [P0-03 最小管理配置、凭据与功能旗标](../../plan/rounds/P0-03.md) | 从控制层向Runtime提供固定配置和当前撤销状态。 | accepted |
| [P0-04 受理、原文、状态、事件与资源账本](../../plan/rounds/P0-04.md) | 保存原文并以真实状态和用量驱动后续执行。 | accepted |
| [P4-04 多层结果缓存与在途合并](../../plan/rounds/P4-04.md) | 在不改变当前权限和结果语义的前提下减少重复工作。 | planned |
| [P4-05 MCP与私人账号连接生命周期](../../plan/rounds/P4-05.md) | 可安装接入能力，但授权由真实账户和政策决定。 | planned |
| [P4-06 完整配置与能力包版本发布](../../plan/rounds/P4-06.md) | 管理员可验证、发布、停用和恢复配置或插件。 | planned |
| [P5-03 完整观测、版本评测与发布候选](../../plan/rounds/P5-03.md) | 用真实结果和成本决定版本是否可试用。 | planned |
| [P5-05 单用户工作区受控试用准备](../../plan/rounds/P5-05.md) | 把可用能力交给真实用户，保留账号和设备边界。 | planned |

关联轮次覆盖主责与协同工作，不等于每轮都实现本模块全部功能。按轮任务/具体能力附真实证据，再核对 [技术兼容与接入验证](../VALIDATION.md)。

## 6. 本模块接口和对象的权威

[逐字段对象字典](../../api/OBJECTS.md) · [通用约束](../../api/CONVENTIONS.md) · [目录与依赖](../../PROJECT_STRUCTURE.md)

技术表描述实现组件，不新增另一套请求字段。需要签名profile、权限、模型范围等新增字段时先修contracts/策略源，再生成文档和兼容验证。

