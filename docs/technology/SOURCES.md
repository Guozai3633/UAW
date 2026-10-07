# 官方资料与方案依据

核对日期：2026-10-07。技术主选是UAW工程设计，官网资料用于核对库的能力/接口；并不证明UAW的组合已经运行。

以下保留官方项目入口。具体SDK供应商/版本、生产配置、许可分发和系统支持在相应实施轮按实际候选继续核对。SDK的main/latest文档可能包含开发版，依赖锁定只使用批准稳定发行版。

| 组件 | 官方入口 | UAW使用方向 |
| --- | --- | --- |
| Python | [python](https://devguide.python.org/versions/) | 七Runtime和本地Runner语言 |
| uv | [uv](https://docs.astral.sh/uv/) | Python依赖、锁文件和项目环境 |
| FastAPI | [fastapi](https://fastapi.tiangolo.com/features/) | HTTP入口、依赖注入与ASGI适配 |
| Uvicorn | [uvicorn](https://github.com/Kludex/uvicorn) | ASGI进程入口 |
| Pydantic | [pydantic](https://docs.pydantic.dev/latest/concepts/strict_mode/) | 严格Python DTO与内部类型 |
| JSON Schema校验器 | [jsonschema](https://python-jsonschema.readthedocs.io/en/stable/) | 执行现有2020-12契约 |
| SQLAlchemy | [sqlalchemy](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html) | 领域Repository与事务适配 |
| Psycopg | [psycopg](https://www.psycopg.org/psycopg3/docs/) | PostgreSQL异步驱动 |
| Alembic | [alembic](https://alembic.sqlalchemy.org/en/latest/) | 人工审阅的数据库迁移 |
| PostgreSQL | [postgres](https://www.postgresql.org/support/versioning/) | 业务状态、CAS、Outbox与持久待办 |
| pgvector | [pgvector](https://github.com/pgvector/pgvector) | 工具/资料/记忆向量索引 |
| pg_trgm/全文检索 | [pgtrgm](https://www.postgresql.org/docs/17/pgtrgm.html) | 关键词、名称与模糊召回 |
| LangGraph | [langgraph](https://docs.langchain.com/oss/python/langgraph/overview) | 单个Agent实例内部循环的执行后端 |
| LangGraph PostgreSQL Checkpointer | [graph_checkpoint](https://docs.langchain.com/oss/python/langgraph/persistence) | 图执行位置；由Run恢复门控制 |
| LangChain组件 | [langchain](https://docs.langchain.com/oss/python/langchain/overview) | 基础抽象按框架依赖；模型/资料集成位于UAW接口之后 |
| HTTPX | [httpx](https://www.python-httpx.org/async/) | 异步联网与连接池 |
| MCP官方Python SDK | [mcp](https://github.com/modelcontextprotocol/python-sdk) | 批准服务的协议session/能力发现/调用 |
| cachetools | [cachetools](https://cachetools.readthedocs.io/en/stable/) | 有界进程缓存；锁和失效由UAW管理 |
| S3 Blob适配 | [s3](https://docs.aws.amazon.com/boto3/latest/reference/services/s3.html) | 后续对象存储后端 |
| structlog | [structlog](https://www.structlog.org/en/stable/) | 结构化脱敏日志 |
| OpenTelemetry | [otel](https://opentelemetry.io/docs/languages/python/) | 跨模块trace和指标接口 |
| Authlib/OIDC | [authlib](https://github.com/authlib/authlib) | 账号登录协议适配 |
| SQLite | [sqlite](https://docs.python.org/3/library/sqlite3.html) | Runner本机命令/回执账本 |
| websockets | [websockets](https://websockets.readthedocs.io/en/stable/) | Runner向后端发起WSS长连接 |
| cryptography/Ed25519 | [cryptography](https://cryptography.io/en/latest/hazmat/primitives/asymmetric/ed25519/) | Runner信封/回执签名 |
| RFC8785规范JSON | [jcs](https://github.com/trailofbits/rfc8785.py) | 双方一致的签名/摘要字节 |
| OS凭据库 | [keyring](https://keyring.readthedocs.io/en/latest/) | 设备私钥及本机秘密存取 |
| psutil | [psutil](https://psutil.readthedocs.io/en/latest/) | 真实进程与资源观测 |
| Windows Job Objects | [job_objects](https://learn.microsoft.com/en-us/windows/win32/procthread/job-objects) | Windows进程组及退出清理 |
| Git CLI | [git](https://git-scm.com/docs/git-worktree) | worktree、差异、三方合并 |
| Docker/Compose | [docker](https://docs.docker.com/engine/security/) | 开发服务编排；可选受控Linux执行模板 |
| PySide6 | [pyside](https://doc.qt.io/qtforpython-6/) | Runner可信本机目录选择/托盘 |
| PyInstaller | [pyinstaller](https://pyinstaller.org/en/stable/operating-mode.html) | Runner按目标OS构建安装包 |
| pypdf | [pypdf](https://pypdf.readthedocs.io/en/stable/user/extract-text.html) | 文本型PDF摄取与页定位 |
| python-docx | [docx](https://python-docx.readthedocs.io/en/latest/) | DOCX内容/报告适配 |
| openpyxl | [xlsx](https://openpyxl.readthedocs.io/en/stable/) | XLSX读写与公式保留 |
| Node.js | [node](https://nodejs.org/en/about/previous-releases) | 前端构建环境 |
| pnpm | [pnpm](https://pnpm.io/installation) | 前端依赖与锁文件 |
| React | [react](https://react.dev/learn) | 聊天与工作区UI |
| TypeScript | [typescript](https://www.typescriptlang.org/docs/) | 前端严格类型 |
| Vite | [vite](https://vite.dev/guide/) | SPA开发与静态构建 |
| Tailwind CSS | [tailwind](https://tailwindcss.com/docs/installation/using-vite) | 产品样式和主题token |
| Radix Primitives | [radix](https://www.radix-ui.com/primitives/docs/overview/introduction) | 对话框/菜单/开关的交互基础 |
| TanStack Query | [query](https://tanstack.com/query/latest/docs/framework/react/overview) | 服务端状态读取/刷新 |
| React Router | [router](https://reactrouter.com/start/declarative/installation) | 项目/会话/成果导航 |
| Monaco Editor | [monaco](https://github.com/microsoft/monaco-editor) | 实际代码/文本Diff查看 |
| react-markdown | [markdown](https://github.com/remarkjs/react-markdown) | 安全报告和引用展示 |
| PDF.js | [pdfjs](https://mozilla.github.io/pdf.js/) | 获准PDF页预览 |
| Ajv | [ajv](https://ajv.js.org/json-schema.html) | 前端2020-12边界校验 |
| openapi-typescript | [openapi_ts](https://openapi-ts.dev/introduction) | 从契约生成HTTP类型/客户端 |
| Dexie/IndexedDB | [dexie](https://dexie.org/docs/) | 账号隔离的页面缓存与草稿 |
| pytest | [pytest](https://docs.pytest.org/en/stable/) | 状态/权限/恢复和真实场景检查 |
| Ruff | [ruff](https://docs.astral.sh/ruff/) | Python格式和静态检查 |
| mypy | [mypy](https://mypy.readthedocs.io/en/stable/) | port/类型依赖检查 |
| Playwright | [playwright](https://playwright.dev/docs/intro) | 真实页面与API事件场景 |
| Nginx | [nginx](https://nginx.org/en/docs/http/ngx_http_proxy_module.html) | 同源静态站点/API/SSE/WSS入口 |

## 协议与关键差异

- [RFC8785](https://www.rfc-editor.org/rfc/rfc8785)：签名字节规范主选；UAW具体profile需双方测试和契约约束。
- [PostgreSQL SELECT/锁](https://www.postgresql.org/docs/17/sql-select.html)：短claim辅助；长期任务控制由UAW租约/栅栏处理。
- [LangGraph持久化](https://docs.langchain.com/oss/python/langgraph/persistence)：局部图状态；跨领域已提交引用和未知副作用由UAW管理。
- [pgvector](https://github.com/pgvector/pgvector)：近似检索/过滤行为需召回评测；查询范围与工具调用授权仍由UAW检查。

