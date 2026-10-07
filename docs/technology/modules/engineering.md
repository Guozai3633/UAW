# 工程、验证与部署 · 技术组件设计

技术v0.1 · 2026-10-07 · 主选设计；实际实施范围见[开发记录](../../implementation/README.md)。

[技术总览](../../../TECHNOLOGY_STACK.md) · [模块索引](../README.md) · [框架边界](../FRAMEWORK_BOUNDARIES.md)

## 1. 主选组件与使用阶段

| 组件 | 实际包/服务 | 在本模块承担什么 | 基线与加入时机 |
| --- | --- | --- | --- |
| [Python](https://devguide.python.org/versions/) | `CPython` | 七Runtime和本地Runner语言 | 3.14.x主线；3.13仅兼容回退候选 / 基础 |
| [uv](https://docs.astral.sh/uv/) | `uv` | Python依赖、锁文件和项目环境 | 稳定版，冻结具体版本 / 基础 |
| [FastAPI](https://fastapi.tiangolo.com/features/) | `fastapi` | HTTP入口、依赖注入与ASGI适配 | 稳定版/Pydantic 2组合 / P0/P1 |
| [Uvicorn](https://github.com/Kludex/uvicorn) | `uvicorn` | ASGI进程入口 | 与FastAPI验证后锁定 / P0/P1 |
| [SQLAlchemy](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html) | `sqlalchemy` | 领域Repository与事务适配 | 2.x异步API / P0 |
| [Alembic](https://alembic.sqlalchemy.org/en/latest/) | `alembic` | 人工审阅的数据库迁移 | 稳定版/SQLAlchemy 2 / P0 |
| [PostgreSQL](https://www.postgresql.org/support/versioning/) | `数据库服务` | 业务状态、CAS、Outbox与持久待办 | 17.x受支持维护线 / P0 |
| [Docker/Compose](https://docs.docker.com/engine/security/) | `系统Docker Engine和Compose插件` | 开发服务编排；可选受控Linux执行模板 | 稳定版/镜像digest固定 / P0部署，任务执行按D03/D09 |
| [Node.js](https://nodejs.org/en/about/previous-releases) | `Node.js` | 前端构建环境 | 24 LTS / P1 |
| [pnpm](https://pnpm.io/installation) | `pnpm` | 前端依赖与锁文件 | 稳定版/Node 24兼容 / P1 |
| [pytest](https://docs.pytest.org/en/stable/) | `pytest/pytest-asyncio` | 状态/权限/恢复和真实场景检查 | 稳定兼容组合 / P0起 |
| [Ruff](https://docs.astral.sh/ruff/) | `ruff` | Python格式和静态检查 | 稳定版 / P0 |
| [mypy](https://mypy.readthedocs.io/en/stable/) | `mypy` | port/类型依赖检查 | 稳定版 / P0 |
| [Playwright](https://playwright.dev/docs/intro) | `@playwright/test` | 真实页面与API事件场景 | 稳定版＋对应浏览器锁定 / P1 |
| [Nginx](https://nginx.org/en/docs/http/ngx_http_proxy_module.html) | `nginx` | 同源静态站点/API/SSE/WSS入口 | 稳定维护线 / P5部署 |
| [structlog](https://www.structlog.org/en/stable/) | `structlog` | 结构化脱敏日志 | 稳定版 / P0，P5完善 |
| [OpenTelemetry](https://opentelemetry.io/docs/languages/python/) | `opentelemetry-api/sdk及OTLP exporter` | 跨模块trace和指标接口 | 兼容稳定组合 / P5 |

表中P4/P5或按需组件不要求首轮全部安装。SDK供应商、账户授权、可选环境和格式仍按产品决策/管理员配置确定；组件主选不会扩大权限。

## 2. 接入、细分职责与实现策略

### 组装和依赖

composition.py是唯一组装根，注入facade需要的ports和批准adapter；domain/public contracts不导入FastAPI、LangGraph或ORM实体。新增infrastructure只装外部组件，不管理任务业务状态。

uv管理Runtime包，前端pnpm管理node依赖，本地Runner用独立锁定环境；普通任务项目另有自己的依赖。P0的pyproject/uv.lock已生成并实际验证；前端/Runner依赖文件在相应阶段生成，不能据此推断整套能力已实现。

### 进程和服务

同一Python项目提供API和后台worker两个入口，单进程开发可启动受控worker协程；试用用独立worker进程，持久待办和租约位于PostgreSQL。worker数量/并发由资源账本约束，不通过增加ASGI worker无意重复启动全部任务。

Docker Compose用于本地API/worker/PG开发集成；生产部署包按D01与具体环境决定。Nginx将Web、API、SSE和WSS放同源入口，SSE关闭代理缓冲并设置心跳/超时。Blob使用持久卷，不随容器删除；备份同时考虑SQL和blob manifest。

### 必要验证

pytest/pytest-asyncio查权限、版本、状态、幂等、取消、解析和恢复边界；Ruff/mypy查接口依赖和类型；Playwright验真实页面。实际模型/Runner/测试/联网回执另保留，不能以单位测试通过替代整条任务。

兼容矩阵至少包括Python/平台wheel、FastAPI/Pydantic/schema、LangGraph/checkpointer/SDK、PostgreSQL/pgvector、React/Vite/Node、Runner签名和安装包。P0锁核心，后续能力各轮锁自己的依赖；发布冻结全套版本与镜像digest。

### 后续扩容

首版不要求Kubernetes、Kafka、独立向量服务、分布式缓存或大规模微服务。出现可测容量瓶颈后通过ports增加服务，并继续保持状态所有者唯一。此限制针对首版默认依赖，已有架构的能力边界保留。

## 3. 架构子节点的具体技术落点

这是架构边界之外的配套实现分组，按上面的组件分工与相关轮次接入；不创建第八个Runtime或新的任务状态所有者。

## 4. 目录与依赖位置

- `src/uaw/composition.py`
- `src/uaw/application.py`
- `src/uaw/infrastructure/`
- `tests/`
- `ops/`
- `docs/decisions/`

目录为完整开发目标，部分工程设施已实现，业务能力以实际记录为准。领域contracts/ports保留UAW类型；第三方库在实现adapter中使用，composition负责组装。框架或ORM对象不能成为跨Runtime公开协议。

## 5. 对应开发轮次与验收

| 工作包 | 本轮职责 | 当前状态 |
| --- | --- | --- |
| [P0-01 工程启动与最小契约](../../plan/rounds/P0-01.md) | 建立能启动的Python应用和依赖组装，避免先实现全部未来DTO。 | accepted |
| [P1-11 第一条真实任务阶段验收](../../plan/rounds/P1-11.md) | 证明从用户输入到检查、变更和接受完整可用。 | planned |
| [P2-09 三类工作与单子任务验收](../../plan/rounds/P2-09.md) | 形成独立UAW的基础产品证据。 | planned |
| [P3-08 规划与并行收益验收](../../plan/rounds/P3-08.md) | 以真实结果证明复杂执行方式何时值得启用。 | planned |
| [P4-10 能力增强与撤销一致性验收](../../plan/rounds/P4-10.md) | 验证效率增强不复活过期权限或影响成果质量。 | planned |
| [P5-03 完整观测、版本评测与发布候选](../../plan/rounds/P5-03.md) | 用真实结果和成本决定版本是否可试用。 | planned |
| [P5-07 交付盘点与开发移交](../../plan/rounds/P5-07.md) | 把实际完成、未完成和默认关闭能力分别列清。 | planned |

关联轮次覆盖主责与协同工作，不等于每轮都实现本模块全部功能。按轮任务/具体能力附真实证据，再核对 [技术兼容与接入验证](../VALIDATION.md)。

## 6. 本模块接口和对象的权威

[逐字段对象字典](../../api/OBJECTS.md) · [通用约束](../../api/CONVENTIONS.md) · [目录与依赖](../../PROJECT_STRUCTURE.md)

技术表描述实现组件，不新增另一套请求字段。需要签名profile、权限、模型范围等新增字段时先修contracts/策略源，再生成文档和兼容验证。

