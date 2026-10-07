# 组件、依赖分组与版本冻结

[技术总览](../../TECHNOLOGY_STACK.md)

采用设计主线＋实际兼容锁文件两层。下表是完整主选；P0核心依赖已按uv.lock安装，实际版本/范围见[环境回执](../implementation/evidence/environment.json)。其余组件按阶段安装；包存在不等于功能已经可用。

## 1. Python依赖组

| 依赖组（计划） | 范围 | 安装时机 |
| --- | --- | --- |
| runtime-core | FastAPI/Uvicorn、Pydantic/jsonschema、SQLAlchemy/Psycopg/Alembic、HTTPX/structlog | P0/P1最小可用子集 |
| agent-engine | LangGraph及PostgreSQL局部checkpointer/受控serializer | P1-07接线；P1-09审批；P5补复合恢复 |
| providers | 管理员批准的官方SDK；按需LangChain集成 | P0-05及实际新增provider轮 |
| retrieval | pgvector适配/批准embedding adapter | P4-03 |
| formats | pypdf、按需DOCX/XLSX适配 | P2及格式启用轮；解析进程独立 |
| connectors | MCP官方SDK及批准session adapter | P4-05 |
| efficiency/telemetry | cachetools、OpenTelemetry等 | P4/P5，基本日志先启用 |
| runner | 独立Python环境；WS/签名/keyring/psutil/PySide、Windows pywin32 | P1起；不塞入任务项目依赖 |
| development | pytest、pytest-asyncio、Ruff、mypy | P0起，不带入任务执行模板 |

后续pyproject中可选依赖组不让代码暗装包；新provider/格式未启用时不会自动变成可发现工具。任务项目依赖单独按锁文件准备。

## 2. Web依赖组

Node 24 LTS＋pnpm；React/TypeScript/Vite、Tailwind/Radix、Query/Router为页面基础。Monaco、PDF.js等按功能懒加载，worker自托管；openapi-typescript负责生成，Ajv2020负责动态边界。Dexie后置到P4，不把登录令牌写IndexedDB。

## 3. 外部服务和系统组件

首个数据后端PostgreSQL 17＋私有Blob持久卷。pgvector/pg_trgm在相关轮启用，数据库image/digest与扩展组合一起记录。模型/搜索/IdP/秘密服务是管理员配置的外部依赖，供应商尚未选定。

Docker/Compose用于开发编排；本机Git和语言工具探测实际版本。Nginx在正式部署接同源TLS/SSE/WSS。首版不额外要求向量服务、Redis/Celery、Kafka或Kubernetes。

## 4. 每个组件的精确职责

| 组件 | 实际包/服务 | 在本模块承担什么 | 基线与加入时机 |
| --- | --- | --- | --- |
| [Python](https://devguide.python.org/versions/) | `CPython` | 七Runtime和本地Runner语言 | 3.14.x主线；3.13仅兼容回退候选 / 基础 |
| [uv](https://docs.astral.sh/uv/) | `uv` | Python依赖、锁文件和项目环境 | 稳定版，冻结具体版本 / 基础 |
| [FastAPI](https://fastapi.tiangolo.com/features/) | `fastapi` | HTTP入口、依赖注入与ASGI适配 | 稳定版/Pydantic 2组合 / P0/P1 |
| [Uvicorn](https://github.com/Kludex/uvicorn) | `uvicorn` | ASGI进程入口 | 与FastAPI验证后锁定 / P0/P1 |
| [Pydantic](https://docs.pydantic.dev/latest/concepts/strict_mode/) | `pydantic` | 严格Python DTO与内部类型 | 2.x / 基础 |
| [JSON Schema校验器](https://python-jsonschema.readthedocs.io/en/stable/) | `jsonschema` | 执行现有2020-12契约 | 4.x / Draft202012Validator / 基础 |
| [SQLAlchemy](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html) | `sqlalchemy` | 领域Repository与事务适配 | 2.x异步API / P0 |
| [Psycopg](https://www.psycopg.org/psycopg3/docs/) | `psycopg` | PostgreSQL异步驱动 | 3.x稳定发行版 / P0 |
| [Alembic](https://alembic.sqlalchemy.org/en/latest/) | `alembic` | 人工审阅的数据库迁移 | 稳定版/SQLAlchemy 2 / P0 |
| [PostgreSQL](https://www.postgresql.org/support/versioning/) | `数据库服务` | 业务状态、CAS、Outbox与持久待办 | 17.x受支持维护线 / P0 |
| [pgvector](https://github.com/pgvector/pgvector) | `PostgreSQL扩展＋pgvector Python适配` | 工具/资料/记忆向量索引 | 0.8或更高稳定线；冻结匹配PG版本 / P4 |
| [pg_trgm/全文检索](https://www.postgresql.org/docs/17/pgtrgm.html) | `PostgreSQL扩展/内置功能` | 关键词、名称与模糊召回 | 与PostgreSQL主版本一致 / P2/P4 |
| [LangGraph](https://docs.langchain.com/oss/python/langgraph/overview) | `langgraph` | 单个Agent实例内部循环的执行后端 | 稳定发行版；不使用main/dev / P1，需边界验证 |
| [LangGraph PostgreSQL Checkpointer](https://docs.langchain.com/oss/python/langgraph/persistence) | `langgraph-checkpoint-postgres` | 图执行位置；由Run恢复门控制 | 与langgraph成组锁定 / P1局部保存；P5复合恢复 |
| [LangChain组件](https://docs.langchain.com/oss/python/langchain/overview) | `langchain-core及选定provider集成包` | 基础抽象按框架依赖；模型/资料集成位于UAW接口之后 | 与LangGraph/SDK兼容组合 / core随依赖；provider集成按需 |
| 批准提供方官方SDK | `管理员所选provider的官方Python包` | 真实文本/工具/结构输出与usage | 每provider独立冻结 / P0-05 |
| [HTTPX](https://www.python-httpx.org/async/) | `httpx` | 异步联网与连接池 | 稳定版 / P0/P2 |
| [MCP官方Python SDK](https://github.com/modelcontextprotocol/python-sdk) | `mcp` | 批准服务的协议session/能力发现/调用 | 已发布稳定版；协议profile另锁 / P4 |
| [cachetools](https://cachetools.readthedocs.io/en/stable/) | `cachetools` | 有界进程缓存；锁和失效由UAW管理 | 稳定版 / P4 |
| FSBlobStore | `UAW自有Python适配器` | 私有数据卷中的不可变大内容 | BlobStorePort v0.1 / P0 |
| [S3 Blob适配](https://docs.aws.amazon.com/boto3/latest/reference/services/s3.html) | `boto3` | 后续对象存储后端 | 稳定版＋提供方能力验证 / 按需 |
| [structlog](https://www.structlog.org/en/stable/) | `structlog` | 结构化脱敏日志 | 稳定版 / P0，P5完善 |
| [OpenTelemetry](https://opentelemetry.io/docs/languages/python/) | `opentelemetry-api/sdk及OTLP exporter` | 跨模块trace和指标接口 | 兼容稳定组合 / P5 |
| [Authlib/OIDC](https://github.com/authlib/authlib) | `authlib` | 账号登录协议适配 | 稳定版；IdP由管理员配置 / P5，开发身份先独立 |
| [SQLite](https://docs.python.org/3/library/sqlite3.html) | `Python sqlite3` | Runner本机命令/回执账本 | 随CPython；本机文件系统 / P1 |
| [websockets](https://websockets.readthedocs.io/en/stable/) | `websockets` | Runner向后端发起WSS长连接 | 稳定版asyncio API / P1/P5 |
| [cryptography/Ed25519](https://cryptography.io/en/latest/hazmat/primitives/asymmetric/ed25519/) | `cryptography` | Runner信封/回执签名 | 稳定版，明确签名profile / P1 |
| [RFC8785规范JSON](https://github.com/trailofbits/rfc8785.py) | `rfc8785` | 双方一致的签名/摘要字节 | 稳定版/JCS约束 / P1 |
| [OS凭据库](https://keyring.readthedocs.io/en/latest/) | `keyring` | 设备私钥及本机秘密存取 | 稳定版/批准OS backend / P1 |
| [psutil](https://psutil.readthedocs.io/en/latest/) | `psutil` | 真实进程与资源观测 | 稳定版/平台wheel验证 / P1 |
| [Windows Job Objects](https://learn.microsoft.com/en-us/windows/win32/procthread/job-objects) | `pywin32` | Windows进程组及退出清理 | 稳定版；仅Windows / P1 |
| [Git CLI](https://git-scm.com/docs/git-worktree) | `系统Git` | worktree、差异、三方合并 | 探测实际版本并记录 / P3 |
| [Docker/Compose](https://docs.docker.com/engine/security/) | `系统Docker Engine和Compose插件` | 开发服务编排；可选受控Linux执行模板 | 稳定版/镜像digest固定 / P0部署，任务执行按D03/D09 |
| [PySide6](https://doc.qt.io/qtforpython-6/) | `PySide6` | Runner可信本机目录选择/托盘 | Qt 6稳定组合 / P1 |
| [PyInstaller](https://pyinstaller.org/en/stable/operating-mode.html) | `pyinstaller` | Runner按目标OS构建安装包 | 稳定版/实际OS构建验证 / P5 |
| [pypdf](https://pypdf.readthedocs.io/en/stable/user/extract-text.html) | `pypdf` | 文本型PDF摄取与页定位 | 稳定版 / P2，格式范围待D05 |
| [python-docx](https://python-docx.readthedocs.io/en/latest/) | `python-docx` | DOCX内容/报告适配 | 稳定版 / 按格式需求启用 |
| [openpyxl](https://openpyxl.readthedocs.io/en/stable/) | `openpyxl` | XLSX读写与公式保留 | 稳定版 / 按格式需求启用 |
| [Node.js](https://nodejs.org/en/about/previous-releases) | `Node.js` | 前端构建环境 | 24 LTS / P1 |
| [pnpm](https://pnpm.io/installation) | `pnpm` | 前端依赖与锁文件 | 稳定版/Node 24兼容 / P1 |
| [React](https://react.dev/learn) | `react/react-dom` | 聊天与工作区UI | 19.x稳定组合 / P1 |
| [TypeScript](https://www.typescriptlang.org/docs/) | `typescript` | 前端严格类型 | 稳定版/strict模式 / P1 |
| [Vite](https://vite.dev/guide/) | `vite/@vitejs/plugin-react` | SPA开发与静态构建 | Node 24兼容稳定版 / P1 |
| [Tailwind CSS](https://tailwindcss.com/docs/installation/using-vite) | `tailwindcss/@tailwindcss/vite` | 产品样式和主题token | 4.x / P1 |
| [Radix Primitives](https://www.radix-ui.com/primitives/docs/overview/introduction) | `所用@radix-ui/react-*包` | 对话框/菜单/开关的交互基础 | 与React兼容稳定版 / P1 |
| [TanStack Query](https://tanstack.com/query/latest/docs/framework/react/overview) | `@tanstack/react-query` | 服务端状态读取/刷新 | 5.x稳定线 / P1 |
| [React Router](https://reactrouter.com/start/declarative/installation) | `react-router` | 项目/会话/成果导航 | 稳定版，declarative模式 / P1 |
| [Monaco Editor](https://github.com/microsoft/monaco-editor) | `monaco-editor` | 实际代码/文本Diff查看 | 稳定版/worker自托管 / P1/P3 |
| [react-markdown](https://github.com/remarkjs/react-markdown) | `react-markdown/remark-gfm` | 安全报告和引用展示 | 稳定版/原始HTML关闭 / P1/P2 |
| [PDF.js](https://mozilla.github.io/pdf.js/) | `pdfjs-dist` | 获准PDF页预览 | 稳定版/worker自托管 / P2，格式范围待D05 |
| [Ajv](https://ajv.js.org/json-schema.html) | `ajv/ajv-formats` | 前端2020-12边界校验 | 8.x / Ajv2020 / P1 |
| [openapi-typescript](https://openapi-ts.dev/introduction) | `openapi-typescript/openapi-fetch` | 从契约生成HTTP类型/客户端 | 稳定版/OpenAPI 3.1验证 / P1 |
| [Dexie/IndexedDB](https://dexie.org/docs/) | `dexie` | 账号隔离的页面缓存与草稿 | 稳定版 / P4 |
| [pytest](https://docs.pytest.org/en/stable/) | `pytest/pytest-asyncio` | 状态/权限/恢复和真实场景检查 | 稳定兼容组合 / P0起 |
| [Ruff](https://docs.astral.sh/ruff/) | `ruff` | Python格式和静态检查 | 稳定版 / P0 |
| [mypy](https://mypy.readthedocs.io/en/stable/) | `mypy` | port/类型依赖检查 | 稳定版 / P0 |
| [Playwright](https://playwright.dev/docs/intro) | `@playwright/test` | 真实页面与API事件场景 | 稳定版＋对应浏览器锁定 / P1 |
| [Nginx](https://nginx.org/en/docs/http/ngx_http_proxy_module.html) | `nginx` | 同源静态站点/API/SSE/WSS入口 | 稳定维护线 / P5部署 |

## 5. 如何冻结与升级

1. 主线Python 3.14、Node 24、PG17；确认目标OS与稳定发行包，形成兼容矩阵。
2. 每轮只安装需要的组，验证DTO、状态与真实能力后写uv.lock/pnpm-lock.yaml、实际系统版本和镜像digest。
3. LangGraph/checkpointer/serializer/provider组合一起回归，不能只升级一个包后默认旧检查点可读。
4. 签名算法、JSONprofile、schema/接口和数据库迁移也进入ReleaseManifest，模型/价格/embedding另有配置版本。
5. 发布保留上一可用包、数据迁移/备份步骤、已知限制与能力开关；自动升级不会授予新增工具或网络权限。

具体补丁、供应商价格和兼容性需要实施轮再核验，本次不伪造版本锁文件或成本结论。

