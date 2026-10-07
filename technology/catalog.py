"""Authored technology choices; installation facts come from implementation evidence."""

import json
from pathlib import Path

EVIDENCE_PATH = Path(__file__).resolve().parents[1] / "docs/implementation/evidence/environment.json"
INSTALLATION = json.loads(EVIDENCE_PATH.read_text(encoding="utf-8")) if EVIDENCE_PATH.is_file() else {}

# Baselines are design targets; exact stable versions are locked after compatibility checks.
COMPONENTS = {}


def c(id, name, package, role, baseline, adoption, source=""):
    actual = INSTALLATION.get("components", {}).get(id, {})
    COMPONENTS[id] = dict(name=name, package=package, role=role, baseline=baseline,
                          adoption=adoption, source=source, installed=actual.get("installed", False),
                          installed_version=actual.get("version"))


c("python", "Python", "CPython", "七Runtime和本地Runner语言", "3.14.x主线；3.13仅兼容回退候选", "基础", "https://devguide.python.org/versions/")
c("uv", "uv", "uv", "Python依赖、锁文件和项目环境", "稳定版，冻结具体版本", "基础", "https://docs.astral.sh/uv/")
c("fastapi", "FastAPI", "fastapi", "HTTP入口、依赖注入与ASGI适配", "稳定版/Pydantic 2组合", "P0/P1", "https://fastapi.tiangolo.com/features/")
c("uvicorn", "Uvicorn", "uvicorn", "ASGI进程入口", "与FastAPI验证后锁定", "P0/P1", "https://github.com/Kludex/uvicorn")
c("pydantic", "Pydantic", "pydantic", "严格Python DTO与内部类型", "2.x", "基础", "https://docs.pydantic.dev/latest/concepts/strict_mode/")
c("jsonschema", "JSON Schema校验器", "jsonschema", "执行现有2020-12契约", "4.x / Draft202012Validator", "基础", "https://python-jsonschema.readthedocs.io/en/stable/")
c("sqlalchemy", "SQLAlchemy", "sqlalchemy", "领域Repository与事务适配", "2.x异步API", "P0", "https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html")
c("psycopg", "Psycopg", "psycopg", "PostgreSQL异步驱动", "3.x稳定发行版", "P0", "https://www.psycopg.org/psycopg3/docs/")
c("alembic", "Alembic", "alembic", "人工审阅的数据库迁移", "稳定版/SQLAlchemy 2", "P0", "https://alembic.sqlalchemy.org/en/latest/")
c("postgres", "PostgreSQL", "数据库服务", "业务状态、CAS、Outbox与持久待办", "17.x受支持维护线", "P0", "https://www.postgresql.org/support/versioning/")
c("pgvector", "pgvector", "PostgreSQL扩展＋pgvector Python适配", "工具/资料/记忆向量索引", "0.8或更高稳定线；冻结匹配PG版本", "P4", "https://github.com/pgvector/pgvector")
c("pgtrgm", "pg_trgm/全文检索", "PostgreSQL扩展/内置功能", "关键词、名称与模糊召回", "与PostgreSQL主版本一致", "P2/P4", "https://www.postgresql.org/docs/17/pgtrgm.html")
c("langgraph", "LangGraph", "langgraph", "单个Agent实例内部循环的执行后端", "稳定发行版；不使用main/dev", "P1，需边界验证", "https://docs.langchain.com/oss/python/langgraph/overview")
c("graph_checkpoint", "LangGraph PostgreSQL Checkpointer", "langgraph-checkpoint-postgres", "图执行位置；由Run恢复门控制", "与langgraph成组锁定", "P1局部保存；P5复合恢复", "https://docs.langchain.com/oss/python/langgraph/persistence")
c("langchain", "LangChain组件", "langchain-core及选定provider集成包", "基础抽象按框架依赖；模型/资料集成位于UAW接口之后", "与LangGraph/SDK兼容组合", "core随依赖；provider集成按需", "https://docs.langchain.com/oss/python/langchain/overview")
c("model_sdk", "批准提供方官方SDK", "管理员所选provider的官方Python包", "真实文本/工具/结构输出与usage", "每provider独立冻结", "P0-05", "")
c("httpx", "HTTPX", "httpx", "异步联网与连接池", "稳定版", "P0/P2", "https://www.python-httpx.org/async/")
c("mcp", "MCP官方Python SDK", "mcp", "批准服务的协议session/能力发现/调用", "已发布稳定版；协议profile另锁", "P4", "https://github.com/modelcontextprotocol/python-sdk")
c("cachetools", "cachetools", "cachetools", "有界进程缓存；锁和失效由UAW管理", "稳定版", "P4", "https://cachetools.readthedocs.io/en/stable/")
c("blob_fs", "FSBlobStore", "UAW自有Python适配器", "私有数据卷中的不可变大内容", "BlobStorePort v0.1", "P0", "")
c("s3", "S3 Blob适配", "boto3", "后续对象存储后端", "稳定版＋提供方能力验证", "按需", "https://docs.aws.amazon.com/boto3/latest/reference/services/s3.html")
c("structlog", "structlog", "structlog", "结构化脱敏日志", "稳定版", "P0，P5完善", "https://www.structlog.org/en/stable/")
c("otel", "OpenTelemetry", "opentelemetry-api/sdk及OTLP exporter", "跨模块trace和指标接口", "兼容稳定组合", "P5", "https://opentelemetry.io/docs/languages/python/")
c("authlib", "Authlib/OIDC", "authlib", "账号登录协议适配", "稳定版；IdP由管理员配置", "P5，开发身份先独立", "https://github.com/authlib/authlib")
c("sqlite", "SQLite", "Python sqlite3", "Runner本机命令/回执账本", "随CPython；本机文件系统", "P1", "https://docs.python.org/3/library/sqlite3.html")
c("websockets", "websockets", "websockets", "Runner向后端发起WSS长连接", "稳定版asyncio API", "P1/P5", "https://websockets.readthedocs.io/en/stable/")
c("cryptography", "cryptography/Ed25519", "cryptography", "Runner信封/回执签名", "稳定版，明确签名profile", "P1", "https://cryptography.io/en/latest/hazmat/primitives/asymmetric/ed25519/")
c("jcs", "RFC8785规范JSON", "rfc8785", "双方一致的签名/摘要字节", "稳定版/JCS约束", "P1", "https://github.com/trailofbits/rfc8785.py")
c("keyring", "OS凭据库", "keyring", "设备私钥及本机秘密存取", "稳定版/批准OS backend", "P1", "https://keyring.readthedocs.io/en/latest/")
c("psutil", "psutil", "psutil", "真实进程与资源观测", "稳定版/平台wheel验证", "P1", "https://psutil.readthedocs.io/en/latest/")
c("job_objects", "Windows Job Objects", "pywin32", "Windows进程组及退出清理", "稳定版；仅Windows", "P1", "https://learn.microsoft.com/en-us/windows/win32/procthread/job-objects")
c("git", "Git CLI", "系统Git", "worktree、差异、三方合并", "探测实际版本并记录", "P3", "https://git-scm.com/docs/git-worktree")
c("docker", "Docker/Compose", "系统Docker Engine和Compose插件", "开发服务编排；可选受控Linux执行模板", "稳定版/镜像digest固定", "P0部署，任务执行按D03/D09", "https://docs.docker.com/engine/security/")
c("pyside", "PySide6", "PySide6", "Runner可信本机目录选择/托盘", "Qt 6稳定组合", "P1", "https://doc.qt.io/qtforpython-6/")
c("pyinstaller", "PyInstaller", "pyinstaller", "Runner按目标OS构建安装包", "稳定版/实际OS构建验证", "P5", "https://pyinstaller.org/en/stable/operating-mode.html")
c("pypdf", "pypdf", "pypdf", "文本型PDF摄取与页定位", "稳定版", "P2，格式范围待D05", "https://pypdf.readthedocs.io/en/stable/user/extract-text.html")
c("docx", "python-docx", "python-docx", "DOCX内容/报告适配", "稳定版", "按格式需求启用", "https://python-docx.readthedocs.io/en/latest/")
c("xlsx", "openpyxl", "openpyxl", "XLSX读写与公式保留", "稳定版", "按格式需求启用", "https://openpyxl.readthedocs.io/en/stable/")
c("node", "Node.js", "Node.js", "前端构建环境", "24 LTS", "P1", "https://nodejs.org/en/about/previous-releases")
c("pnpm", "pnpm", "pnpm", "前端依赖与锁文件", "稳定版/Node 24兼容", "P1", "https://pnpm.io/installation")
c("react", "React", "react/react-dom", "聊天与工作区UI", "19.x稳定组合", "P1", "https://react.dev/learn")
c("typescript", "TypeScript", "typescript", "前端严格类型", "稳定版/strict模式", "P1", "https://www.typescriptlang.org/docs/")
c("vite", "Vite", "vite/@vitejs/plugin-react", "SPA开发与静态构建", "Node 24兼容稳定版", "P1", "https://vite.dev/guide/")
c("tailwind", "Tailwind CSS", "tailwindcss/@tailwindcss/vite", "产品样式和主题token", "4.x", "P1", "https://tailwindcss.com/docs/installation/using-vite")
c("radix", "Radix Primitives", "所用@radix-ui/react-*包", "对话框/菜单/开关的交互基础", "与React兼容稳定版", "P1", "https://www.radix-ui.com/primitives/docs/overview/introduction")
c("query", "TanStack Query", "@tanstack/react-query", "服务端状态读取/刷新", "5.x稳定线", "P1", "https://tanstack.com/query/latest/docs/framework/react/overview")
c("router", "React Router", "react-router", "项目/会话/成果导航", "稳定版，declarative模式", "P1", "https://reactrouter.com/start/declarative/installation")
c("monaco", "Monaco Editor", "monaco-editor", "实际代码/文本Diff查看", "稳定版/worker自托管", "P1/P3", "https://github.com/microsoft/monaco-editor")
c("markdown", "react-markdown", "react-markdown/remark-gfm", "安全报告和引用展示", "稳定版/原始HTML关闭", "P1/P2", "https://github.com/remarkjs/react-markdown")
c("pdfjs", "PDF.js", "pdfjs-dist", "获准PDF页预览", "稳定版/worker自托管", "P2，格式范围待D05", "https://mozilla.github.io/pdf.js/")
c("ajv", "Ajv", "ajv/ajv-formats", "前端2020-12边界校验", "8.x / Ajv2020", "P1", "https://ajv.js.org/json-schema.html")
c("openapi_ts", "openapi-typescript", "openapi-typescript/openapi-fetch", "从契约生成HTTP类型/客户端", "稳定版/OpenAPI 3.1验证", "P1", "https://openapi-ts.dev/introduction")
c("dexie", "Dexie/IndexedDB", "dexie", "账号隔离的页面缓存与草稿", "稳定版", "P4", "https://dexie.org/docs/")
c("pytest", "pytest", "pytest/pytest-asyncio", "状态/权限/恢复和真实场景检查", "稳定兼容组合", "P0起", "https://docs.pytest.org/en/stable/")
c("ruff", "Ruff", "ruff", "Python格式和静态检查", "稳定版", "P0", "https://docs.astral.sh/ruff/")
c("mypy", "mypy", "mypy", "port/类型依赖检查", "稳定版", "P0", "https://mypy.readthedocs.io/en/stable/")
c("playwright", "Playwright", "@playwright/test", "真实页面与API事件场景", "稳定版＋对应浏览器锁定", "P1", "https://playwright.dev/docs/intro")
c("nginx", "Nginx", "nginx", "同源静态站点/API/SSE/WSS入口", "稳定维护线", "P5部署", "https://nginx.org/en/docs/http/ngx_http_proxy_module.html")

MODULES = {}


def m(id, name, roots, components, paths, rounds, text):
    MODULES[id] = dict(name=name, roots=roots.split(), components=components.split(),
                       paths=paths, extra_rounds=rounds.split(), strategy=text.strip())


m("intent", "Intent：用户问题加工", "intent", "python pydantic jsonschema sqlalchemy postgres", ["src/uaw/intent/", "prompts/"], "", """
### 技术怎样串起来

原文从Run读取 → 按目的向Context取资料 → 通过ModelGateway请求当前继承模型 → jsonschema验证结构 → 原文含义/引用/修订核验 → Repository按CAS提交TaskFrame。

模型输出只能作为理解提案。TaskFrame持久化与原文追加存储分别归Intent/Run；不引入另一个LangChain会话历史。语义解析、指代和歧义用当前模型，路径/版本/字段检查用Python。探查材料通过Tool facade。

### 子组件策略

- Preview：短延迟debounce、草稿revision、任务取消和有效期由自有控制器处理。服务端只读、低预算；模型仍继承用户选择。页面仅接受当前草稿revision。
- Original/Frame：不可变原文Ref、补充来源和框架revision可追溯，SQL更新带预期版本。不能覆盖用户原文。
- Semantic/References/Ambiguity：短模板按需加载。结构错误有界反馈，语义不确定明确记录；不靠词典或输入长度分档。
- Probe：只有确有信息缺口时发现并调用获准工具，不直接绕Tool访问文件或联网。

### 状态与替换边界

无框架专属状态。更换模型adapter或Agent执行引擎，不改变TaskFrame与原文协议。预览缓存只复用同草稿/相同配置依赖，不能拿草稿结果直接作为正式TaskFrame提交。
""")

m("agent", "Agent：主循环、角色与协作", "agent", "python pydantic jsonschema langgraph graph_checkpoint sqlalchemy postgres pgvector pgtrgm", ["src/uaw/agent/", "src/uaw/agent/engines/", "src/uaw/tool/control/", "capabilities/builtin/"], "", """
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
""")

m("context", "Context：资料、上下文与记忆", "context", "python pydantic jsonschema sqlalchemy postgres pgvector pgtrgm pypdf docx xlsx blob_fs", ["src/uaw/context/", "src/uaw/context/readers/", "src/uaw/context/parsers/", "src/uaw/context/indexes/"], "", """
### 摄取与引用

Reader port读取获准历史、Board、Workspace及外部资料；本地内容来自Runner。先校验真实格式/大小/范围，再在受限parser进程解析；产出内容Hash、提取器版本、片段位置和原始Ref。

首批建议TXT/Markdown和文本型PDF，最终格式范围依D05。pypdf保留页及提取文本偏移；版面行号和扫描件OCR能力另报告，不用猜测补全文本。python-docx/openpyxl为DOCX/XLSX适配主选，按实际格式启用。openpyxl不负责公式计算；需要重算时另接获准执行环境并留下真实检查回执。

对象、片段、Reference和索引版本在PostgreSQL；大内容入BlobStore。文件摄取事务提交成功后才发布可检索修订，故障留下可清理的未引用blob。

### 召回与上下文装配

小资料集先精确/关键词召回，P4用pgvector结合关键词结果做RRF融合。embedding由批准profile配置，记录模型/维度/归一化/内容版本，不同profile不混算距离。embedding服务是检索能力，不成为额外回答/审批Agent；语义判断仍继承用户LLM。

英语正文可用PostgreSQL FTS；中文工具描述/短文本用规范化名称、精确/子串、字符n-gram召回适配，再融合向量。默认英语分词不能宣称覆盖中文；短词检索做有界候选查询。扩大资料规模前按中文/英文样例评测。

Composer保留来源/优先级、硬约束、真实执行状态和输出空间；工具schema只来自当前可用目录。TokenCounter通过提供方adapter估算或查询，不能用一个tokenizer精确代表所有模型。

### 记忆与压缩

MemoryCandidate经当前模型提议，policy/conflict/version由Python与SQL落实；读、贡献、删除分别控制。删除立刻阻断后续取用并失效派生缓存/摘要，物理清理按回执处理。

语义压缩通过ModelGateway，依赖Manifest记录来源版本；自有核验保留数字/路径/要求/未决动作。LangChain/LangGraph自动memory或自动摘要不独立接管Context。模型输入由此唯一装配后交Model。
""")

m("tool", "Tool：发现、执行与失败治理", "tool", "python pydantic jsonschema sqlalchemy postgres pgvector pgtrgm httpx mcp", ["src/uaw/tool/", "src/uaw/tool/control/", "src/uaw/tool/providers/"], "", """
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
""")

m("workspace", "Workspace：项目、环境与交付", "workspace", "python pydantic jsonschema sqlalchemy postgres blob_fs websockets git docker", ["src/uaw/workspace/", "src/uaw/workspace/backends/", "apps/local_runner/uaw_runner/"], "", """
### 后端和真实能力

LocalBackend主选经签名Runner协议执行；isolated_copy用于非Git基础隔离，P3加入Git CLI worktree/三方合并。native模式和受控Linux容器模式分别报告实际范围；权限来自本机批准。副本/worktree隔离写冲突，不提供OS访问隔离。

Python Runtime服务不执行任务代码。Docker用于开发服务编排与可选执行模板时分别配置；任务容器不挂控制面凭据或Docker socket。云执行后端只保留port，D09选定供应商并真实验收后启用。

### 数据与环境

Binding元数据、BaseState、Environment、ChangeSet、Artifact和ReviewSet在SQL；获准本机路径映射和执行账本在Runner。基础快照包含用户未提交文件、排除规则和Hash，不能只从HEAD启动。

环境先inspect用户现有Python/Go/Node工具链，再按批准模板ensure。Runtime用uv锁自己的依赖；任务项目依赖按它自己的锁文件/venv/go.mod处理，环境安装与系统权限单独审批。系统apt/nvm等不是无约束通用安装工具。

### 差异、合并和撤销

实际前后字节Hash与shell造成的修改构成ChangeSet。文本差异可用difflib/Git CLI，UI用Monaco；二进制按文件处理。持久review unit由UAW生成，不能把编辑器临时行号当稳定改动ID。

合并按base/候选/当前三方比较，原子写前再次校验文件Handle/Hash，必要时在同根暂存后替换。并行writer有独立工作区和租约。局部接受和revert只处理选择的unit，保留后续用户编辑；影响证据失效并重验。

下载/预览通过Artifact/Reference resolver，不把模型输出路径直接拼成可读URL。文档/表格格式适配按output contract注册；存在或能打开不等于专业质量已过。
""")

m("model", "Model：模型政策与实际调用", "model", "python pydantic jsonschema model_sdk httpx langchain sqlalchemy postgres", ["src/uaw/model/", "src/uaw/model/providers/"], "", """
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
""")

m("run", "Run：历史、审批与恢复", "run", "python pydantic jsonschema sqlalchemy psycopg postgres graph_checkpoint structlog", ["src/uaw/run/", "src/uaw/run/resume/", "src/uaw/infrastructure/db/"], "", """
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
""")

m("support", "共享设施：存储、缓存、配置与观测", "support", "python pydantic jsonschema sqlalchemy psycopg alembic postgres blob_fs s3 cachetools keyring cryptography structlog otel pytest", ["src/uaw/shared/", "src/uaw/infrastructure/", "capabilities/", "ops/"], "", """
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
""")

m("api", "API与账号入口", "ingress", "python fastapi uvicorn pydantic jsonschema authlib sqlalchemy postgres", ["src/uaw/api/", "src/uaw/infrastructure/identity/", "src/uaw/infrastructure/http/"], "P0-03 P1-10 P5-05", """
### HTTP、事件流与设备连接

FastAPI处理认证、输入、归属、配额和Run受理，返回既有业务Envelope；不在请求handler里跑完整长任务。InteractionItem/Event读当前授权后以SSE输出，断线用持久seq/cursor恢复。

Runner协议用受认证WSS双向长连接；配对/连接HTTP路由在实现轮加入契约源，现有设计消息契约不能当作已经部署路由。API不会执行任意本地路径或shell。

### 契约与运行路由

contracts/interface_catalog.py继续作为字段权威。优先实现实际任务所需DTO，Pydantic strict/extra=forbid与jsonschema在边界核验；特定JSON解析的宽松转换也要被统一schema约束。

运行OpenAPI从实际路由生成，并与设计契约中已实现子集做兼容检查。设计81个HTTP操作不自动注册81个成功占位handler。权限来自认证依赖生成TrustedExecutionContext，业务参数不能填admin/approved。

### 身份主选

账号接入选Authlib OIDC adapter，IdP部署/供应商仍由管理员确定。后端处理授权码、state/nonce/PKCE和回调校验，服务端会话cookie为HttpOnly/Secure，账户资源由主体条件限制。

Web与API同源部署，修改动作校验Origin和CSRF token。浏览器缓存不保存平台或第三方令牌。P0仅本机可达开发主体允许独立推进；公网试用前必须接真实身份，OIDC库不自动提供账户产品。

### 失败和限流

SSE慢消费者有界缓冲，超过保留窗口用授权快照续接；一次接收的事件重复不创建重复UI项。断开页面不代表取消Run，取消走明确控制接口。管理员接口单独验证角色，不暴露普通Agent调用。
""")

m("web", "Web：聊天、成果与用户控制", "ui", "node pnpm react typescript vite tailwind radix query router monaco markdown pdfjs ajv openapi_ts dexie playwright", ["apps/web/src/features/", "apps/web/src/lib/api/", "apps/web/src/lib/events/", "apps/web/src/lib/cache/", "apps/web/src/components/"], "P1-10 P2-08 P3-06 P3-07 P4-09 P5-05", """
### 页面骨架

React+TypeScript+Vite做SPA，Tailwind主题token与Radix交互组件组成自有视觉层。React Router负责项目/会话/成果导航；TanStack Query管服务端读取，组件局部状态管草稿和展开。首版不再叠加独立SSR服务或多个全局状态库。

主界面保留会话侧栏、聊天、输入框上方浅色理解提示、成果/变更侧区。‘努力奔跑中’等文案由真实事件状态映射，事实进度和需介入事项仍显示；动画系统后续单独设计。

### 类型、事件和缓存

openapi-typescript/openapi-fetch从已实现API契约生成客户端。Ajv2020校验SSE/Runner展示数据等动态载荷，不能用默认draft-07模式加载2020-12；自定义format显式登记，未知格式不能静默跳过。

事件客户端用fetch ReadableStream解析SSE，支持AbortController、cursor、重复seq去重和最终快照；ItemReducer从协议更新内容，不能解析LLM文字猜命令完成或进度百分比。

Query cache是读取投影。P4用Dexie/IndexedDB保存显式允许的草稿/近期页面投影，按issuer/subject/workspace/配置纪元分区；退出/换账号/撤销清理。令牌、审批与权威Run状态不持久缓存；离线只显示标明版本的内容，不继续执行获准动作。

### 变更与引用

Monaco Diff展示实际ChangeSet，局部选择以服务端unit ID提交，版本Hash/CAS由Workspace决定。react-markdown禁用原始HTML并校验URL协议；PDF.js按获准Reference取内容，worker与资源自托管。

生成HTML预览置独立受限来源/iframe，不携带控制面cookie；可执行脚本、联网等能力另限制。引用走ReferenceResolver，未知本地路径不能点击读取。局部接受、撤销、模型继承和memory开关各自对应真实API。

### 页面验证

Playwright验收真实提交/审批/取消/SSE重连/Diff/局部接受/角色创建及权限拒绝。Mock用于控件错误分支，阶段验收另保存真实后端和模型回执。UI可展示可信状态，不代替后端授权。
""")

m("runner", "本地Runner：设备、文件与进程", "", "python uv pydantic jsonschema sqlite websockets cryptography jcs keyring psutil job_objects pyside git docker pyinstaller", ["apps/local_runner/uaw_runner/", "apps/local_runner/uaw_runner/ui/", "apps/local_runner/uaw_runner/platforms/"], "P1-04 P1-05 P3-05 P4-07 P5-02 P5-05", """
### 本机程序形态

Python执行服务＋PySide6小型托盘/目录选择helper，不要求先构建完整桌面聊天壳。Qt主线程管用户交互，执行服务用独立asyncio进程；通过受认证本机IPC传可信选择结果，UI进程不得成为任意路径执行器。

服务主动建立WSS连接，不默认开放匿名localhost执行HTTP端口。SQLite本机账本保存command受理/真实attempt/进程身份/输出cursor/回执及根handle映射；不会把它用作服务端聊天历史的第二个主库。

### 配对、签名和秘密

设备密钥由cryptography Ed25519生成，keyring必须选可验证的OS凭据backend，无可用安全backend时阻断配对而不退为明文。服务签发命令和设备签发回执分别验证。

签名profile主选RFC8785 JCS字节、SHA-256内容摘要、Ed25519签名，命令/回执加不同域标记并覆盖设备/主体/版本/期限/栅栏。rfc8785严格拒绝不支持的数字和类型；超安全整数/非有限数的字段约束在实施轮补进契约，禁止双方各自四舍五入。

RootSelection只由真实本机交互签发，服务和设备绑定revision分别核验。文件访问用解析后的根及文件Handle防链接/竞态越界；路径resolve字符串检查不提供任意进程的OS隔离。

### 真实进程和停止

asyncio subprocess argv路径启动，获准shell命令显式选择对应执行模式。Windows用Job Objects/pywin32管理进程组，psutil观测CPU/内存/退出和进程身份；PID必须结合启动时间，避免重启后误认重用PID。

Linux执行模板用进程组/容器退出回执；任务代码与Runner账本/设备秘密隔离。没有OS沙箱时native模式明确展示范围，Job Objects不是文件/网络沙箱。断线不等于进程停止；重连查原command，不重复启动unknown动作。

### 发布与回收

PyInstaller按Windows/Linux/macOS分别构建和签发包；不把一次Windows构建称为支持所有平台。初期Windows优先，Linux执行模板验证，macOS再做平台验收。升级保留设备身份/账本兼容，任务目录清理先处理后台进程并保留成果。
""")

m("engineering", "工程、验证与部署", "", "python uv fastapi uvicorn sqlalchemy alembic postgres docker node pnpm pytest ruff mypy playwright nginx structlog otel", ["src/uaw/composition.py", "src/uaw/application.py", "src/uaw/infrastructure/", "tests/", "ops/", "docs/decisions/"], "P0-01 P1-11 P2-09 P3-08 P4-10 P5-03 P5-07", """
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
""")

m("integration", "后续推特包装", "", "python fastapi httpx pydantic jsonschema", ["extensions/twitter/", "docs/integrations/"], "P5-06", """
### 接入边界

先复用UAW受理、会话、控制、成果和审批API，再确定X是请求渠道还是社媒业务产品。平台SDK/API配额、授权和发布协议需届时核对官方资料，当前不选择或调用真实X账户。

渠道adapter将外部事件映射到既有原文/主体/任务请求，明确来源与幂等键；业务发布必须走ToolRuntime效果账本。产品flag关闭不适用的代码/本地能力，不能改变UAW固定模型、权限或完成判断。

P5-06仍是后续设计范围，暂无推特实现、自动发布或运营流水线；核心UAW交付不等待此适配。
""")

BINDINGS = {}


def b(nodes, components, approach):
    for node in nodes.split():
        assert node not in BINDINGS, node
        BINDINGS[node] = dict(components=components.split(), implementation=approach)


b("ui", "react typescript vite tailwind radix query router ajv openapi_ts", "真实Item/Event驱动页面，详情按需展开；技术模块web")
b("ingress", "fastapi uvicorn pydantic jsonschema authlib", "认证依赖注入可信上下文，SSE/WSS适配；技术模块api")
b("intent intent.original intent.frame", "python pydantic jsonschema sqlalchemy postgres", "原文Ref/理解版本与CAS，自有facade")
b("intent.preview intent.semantic intent.references intent.ambiguity", "python pydantic jsonschema", "通过ModelGateway做语义提案，原文/版本/来源用代码校验")
b("intent.probe", "python pydantic", "通过Tool port按需探查，不能直接执行本地/网络动作")
b("agent", "python pydantic langgraph postgres", "自有AgentRuntime，EnginePort封装局部循环")
b("agent.loop", "python langgraph", "StateGraph调用UAW ports，动作条件由LLM选择")
b("agent.assessment agent.definitions.designer agent.definitions.model_intent agent.completion.semantic", "python pydantic jsonschema", "当前继承模型语义提案＋自有范围/来源校验")
b("agent.planning agent.scheduler", "python pydantic postgres", "自有版本化Plan、graphlib无环辅助、asyncio有界调度")
b("agent.definitions agent.definitions.validator agent.definitions.repository agent.definitions.change_service", "python pydantic jsonschema sqlalchemy postgres", "create/update/diff/revert是会话定义服务，定义不等于实例")
b("agent.definitions.discovery", "python postgres pgvector pgtrgm", "会话内候选摘要发现，向量按P4加入，LLM选择invoke")
b("agent.factory agent.collaboration agent.collaboration.contract agent.collaboration.instance", "python pydantic postgres langgraph", "有界实例工厂/权限预算交集；每实例独立Engine和图命名空间")
b("agent.collaboration.channel agent.collaboration.join agent.collaboration.handoff agent.collaboration.cancel agent.board", "python pydantic sqlalchemy postgres", "版本Ref/共享板/CAS控制租约，Run取消传播，父汇总验收")
b("agent.skills", "python pydantic jsonschema", "自有批准SkillLoader/Manifest，按需加载方法与模板")
b("agent.completion agent.completion.contract agent.completion.evidence agent.completion.version agent.completion.delivery agent.completion.acceptance", "python pydantic jsonschema sqlalchemy postgres", "自有完成控制器核验实际Ref/版本，用户接受独立记录")
b("context context.sources context.rules context.selection context.composer context.references", "python pydantic sqlalchemy postgres", "获准Reader/指令优先级/TokenCounter/Manifest，自有上下文入口")
b("context.ingestion", "python pypdf docx xlsx blob_fs postgres", "受限解析器输出版本与位置；格式按D05启用")
b("context.retrieval", "python postgres pgvector pgtrgm", "访问范围内关键词＋向量RRF召回，embedding版本分区")
b("context.compression context.memory.candidate", "python pydantic jsonschema", "经ModelGateway提案，保护关键约束/来源/未决动作")
b("context.memory context.memory.policy context.memory.conflict context.memory.store context.memory.forget", "python pydantic sqlalchemy postgres pgvector", "记忆读写/版本/冲突/删除，索引及缓存依赖失效")
b("tool tool.registry tool.discovery", "python pydantic jsonschema postgres pgvector pgtrgm", "ToolSpec权威注册，权限过滤与混合索引；LLM最终选择")
b("tool.invocation tool.invocation.precheck tool.invocation.approval tool.invocation.recheck tool.invocation.dispatch", "python pydantic postgres", "统一InvocationGate调用自有Policy/Run审批/提供方adapter")
b("tool.invocation.schema", "python jsonschema pydantic", "从统一schema验证准确动作分支，拒绝自报信任字段")
b("tool.invocation.result tool.results tool.effects tool.audit", "python pydantic sqlalchemy postgres blob_fs", "typed回执、真实输出Ref、效果/审计账本与幂等对账")
b("tool.failure", "python postgres", "自有attempt/退避/熔断/严格等价恢复控制器")
b("tool.adapters", "python httpx", "批准provider与Runtime control adapters；持久operation边界")
b("tool.mcp tool.mcp.provider tool.mcp.session tool.mcp.capabilities tool.mcp.invoke tool.mcp.invalidate", "python mcp pydantic postgres", "官方SDK session在统一闸门后，连接/能力撤销失效")
b("workspace workspace.binding", "python pydantic postgres websockets", "LocalBackend通过签名Runner协议；绑定只来自真实选择")
b("workspace.base workspace.isolation", "python postgres blob_fs git docker", "输入快照/独立副本/worktree；可选受控OS后端报告真实能力")
b("workspace.environment workspace.process", "python pydantic websockets", "Runner进程/模板inspect/ensure，实际工具链和回执")
b("workspace.changes workspace.review", "python postgres git", "实际字节Hash、三方合并、稳定review units、局部接受/撤销")
b("workspace.artifacts", "python pydantic postgres blob_fs s3", "产物版本/保留/授权resolver；可选S3 adapter")
b("model model.catalog model.policy model.capability model.usage", "python pydantic jsonschema sqlalchemy postgres", "自有模型继承/能力目录/价格版本与全部attempt账本")
b("model.gateway model.adapters", "python model_sdk httpx langchain", "批准官方SDK主路径；LangChain按需隔离在adapter内")
b("model.recovery", "python postgres", "固定模型或明确Auto集合内恢复，拒绝隐式替换")
b("run run.history run.state run.events run.budget run.approval run.cancel run.trigger", "python pydantic sqlalchemy postgres", "Run领域权威、事务Outbox、SQL待办、审批和控制意图")
b("run.checkpoint", "python postgres graph_checkpoint", "已保存图位置＋已提交领域Ref组成发布检查点")
b("run.resume run.resume.lease run.resume.versions run.resume.access run.resume.effects run.resume.workspace run.resume.continue", "python pydantic postgres graph_checkpoint", "先租约/当前授权/效果与工作区核验，再恢复Engine")
b("support", "python pydantic", "独立共享ports和控制层入口，不增加万能Runtime")
b("support.configuration", "python pydantic jsonschema postgres keyring cryptography", "配置修订/激活/撤销和CredentialStore，部署秘密backend独立")
b("support.extensions", "python pydantic jsonschema postgres", "自有能力Manifest/来源/Hash/依赖/回滚；安装不授予权限")
b("support.cache", "python cachetools postgres blob_fs", "L1＋可持久派生结果，依赖epoch和single-flight由UAW实现")
b("support.observability", "python structlog otel", "脱敏关联日志与版本/attempt trace，默认不导出内容")
b("support.evaluation", "python pytest postgres", "版本场景、真实回执、人工/语义grader与发布阈值")
b("support.stores", "python sqlalchemy psycopg alembic postgres blob_fs s3", "领域Repository适配、迁移、事务、Blob/Index ports")
