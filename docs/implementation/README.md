# 当前实现与开发启动

2026-10-09最新阶段：[MS-I2h-A2](MS-I2h-A2.md)已接受三组件审阅/合入及A接线，421不同聚焦节点通过；历史完整1077仍为ms-i2g。根Agent已看见过滤后的工具定义，JSON-object模式保留本地schema验证。真实DeepSeek已接入；[MS-I2h-A3](MS-I2h-A3.md)有13次真实调用和三个最终任务样例、31个不同聚焦检查。首次失败及修复保留；默认flags与公开入口未开放。

以下为前阶段MS-I2h-A1记录；三份新组件的当前接受状态以MS-I2h-A2为准。

2026-10-09：A的MS-I2h-A1根Agent/有限步动态循环开发组件接受；23单元＋12 Agent SQL＋1原Model兼容SQL，去重36个通过节点，原失败及修复记录保留。历史完整1077覆盖仍属于ms-i2g，本阶段没有重新全量。真实LLM、完整交付、生产认证/IPC/用户确认和正式前端未验收。

本轮方法/目录：[A接线说明](../coordination/requests/A/MS-I2h-Agent-wiring.md)；实际回执：[MS-I2h-A1](MS-I2h-A1.md)；用户视角：[当前进度](PROGRESS-2026-10-09.md)。B/MS-C6、C/MS-T2e、D/MS-R2e已在A2按组件接受；本段A1回执仍属历史。默认公开Runtime绑定与flags未变。

上一完整范围见[MS-I2g](MS-I2g.md)，固定worker开工标签仍为ms-i2h-start。各次历史源代码与回执保留在旧标签，不累加为产品完成百分比。

## 已实现的代码

- Python 3.14项目、uv.lock、FastAPI启动/关闭及真实HTTP健康检查。
- 源码包和wheel已经实际构建；分发包包含运行所需的权威schema副本。
- 公共ID/Ref/Failure/Principal/Scope/RequestMeta/可信上下文子集；复用权威JSON Schema并严格处理未知字段、格式、重复键和非JSON数值。
- 七Runtime的注入port与未实现能力状态；不会给模型注册空实现工具。
- PostgreSQL迁移、主体分区、CAS、请求去重、不可变修订及逻辑删除。
- 同域数据与Outbox事务提交、SQL消费者回执去重。
- 私有不可变blob的主体分区、大小/摘要验证和并发写入。
- 开发 bearer 用户/管理员身份、Windows 凭据库存取、配置校验发布与当前撤销闸门。
- 22个开发HTTP入口和Run公共创建入口；原文、模型选择来源、任务、根预算、交互项与事件事务受理。
- 每attempt预算准入、调用意图、未知用量保留、失败结算及去重核对。
- ModelRuntime.generate与显式Chat Completions adapter；固定模型/能力复核、长输出Blob、结构输出校验、有限重试、取消和未知费用记账。实际LLM调用需要管理员批准配置。
- IntentRuntime.understand/revise与当前frame读取；保留完整用户原文、逐字来源和理解历史，新输入/取消/期限/CAS阻止旧提案提交。旧Run不静默补来源。
- Context来源/规则/窗口组件已通过真实Run/政策/目录adapter接入理解，Intent与Model共用resolver；通用build仍未绑定。Model在准入前计入完整原生请求的保守估算。
- Context通用快照/引用仓储、Composer和References组件已通过实际SQL验证；生产authority/能力Reader尚未注入，通用Context仍未绑定。
- 人工单次审批持久化与认证查询/决定/执行前复核；默认缺Tool动作权限adapter则拒绝，不自动发送工具。
- 实时父子权限链统一检查：Context/Model/Approval共用，八级内逐级核对当前版本、范围/网络收窄和deny；Model工作中撤销父政策会停止本地调用，未知费用保留。
- Tool可信固定回执核对、独立费用恢复及BudgetState/ExecutionPolicy公开port消费已通过43项真实SQL；实际Reader/dispatch未注入。
- PostgreSQL根执行租约与按真实binding命名空间的Model输入路由已验证；lease不是执行权限，通用Context authority仍缺失。
- Tool固定目录、持久调用账本、审批/预算恢复组件；Runner真实签名、当前key撤销、开发配对状态一次使用CAS已合入。预算恢复读port已有真实SQL实现。生产工具目录为空，实际配对/IPC/服务端设备key目录和执行尚未接入。

- Runner平台设备归属/不可变命令登记、预算真实dispatch状态和异步当前权威组件已验证；Container内部服务已组装，缺真实channel/root/gate/signing后端仍不可用。

[开发控制层操作说明](CONTROL_PLANE.md) 包含管理员配置流程、请求格式和本轮限制。

## 安装和启动（PowerShell，在项目根目录）

```powershell
$env:UV_CACHE_DIR = "$PWD/.cache/uv"
$env:UV_PYTHON_INSTALL_DIR = "$PWD/.cache/python"
$env:UV_PYTHON_BIN_DIR = "$PWD/.cache/bin"
uv python install 3.14
uv sync --frozen --extra agent-engine

# 仅启动工程入口
./ops/start.ps1

# 或：启动本机开发数据库、迁移及后端
./ops/start.ps1 -WithPostgres
```

访问 `http://127.0.0.1:8000/health/live` 和 `/health/ready`。ready表示当前控制层/存储准备好；Run、Model和Intent协议入口已绑定，其余四个Runtime未接入。绑定状态不证明供应商连通或自动执行任务；实连见[模型连接说明](MODEL_CONNECTION.md)。Ctrl+C关闭后端；数据库保留。

首次数据库启动需要Docker Desktop。实例名为uaw-development-postgres-1，只绑定127.0.0.1:55432，密码由脚本生成并存于忽略的.data/dev-db.env；脚本把连接URL设置到当前进程环境，不写入版本化配置。没有部署云服务，也没有修改系统Python。

## 验证

```powershell
./ops/check.ps1 -WithPostgres
```

此命令要求真实PostgreSQL，运行静态/类型检查、迁移与必要场景测试，并保存JUnit回执。不加WithPostgres时可运行独立测试；数据库未配置的跳过项不能作为持久化验收证据。开发任务fixture中的故意缺陷不属于Runtime测试集。

真实检查记录见 [P0-01](P0-01.md)、[P0-02](P0-02.md)、[P0-03](P0-03.md)、[P0-04](P0-04.md)、[P0-05](P0-05.md)、[锁定环境](evidence/environment.json) 和 [测试回执](evidence/p0-tests.xml)。P0-05协议fixture和loopback HTTP不作为实际LLM回执。

## 数据维护

- 迁移：设置UAW_DATABASE_URL后执行 `.venv/Scripts/python.exe -m alembic upgrade head`；应用启动只检查版本，不自动改表。
- PostgreSQL备份：在数据库容器中用pg_dump生成归档，再docker cp到.data/backups；命令见[数据维护说明](DATA_OPERATIONS.md)。
- Blob卷单独备份，并保留SQL引用与内容Hash对应关系；恢复后逐项摘要核验。
- 本轮只验证进程重读与事务回滚，不宣称已经完成P5的跨模块崩溃恢复、全量备份恢复或生产部署验收。

## 后续工作

补齐D06提供方/模型/私有凭据与真实调用回执，完成P0-05及Intent语义验收。B开发固定快照/引用，A落实Tool/Runner公共接线后派发C/D下一包，随后接Agent闭环。办公、学术和代码样例在后续真实任务阶段验收。组件基线通过不代表已经通过P0真实模型门槛。

最新内部服务：[执行租约与输入路由](../coordination/requests/A/MS-I2d-ports.md)。租约/fence仅协调workers，不能代替权限或真实执行授权。

## 本轮并行准备（未完成新功能包）

2026-10-08：用户已确认B/C/D均同步ms-i2f2。新完整能力包MS-C5/MS-T2d/MS-R2d已发布；固定环境准备标签ms-i2g-start。A旧数据库兼容及8项SQL复验通过，新worker独立库由各自启动。

841项是ms-i2f2运行代码的完整回执，本次环境/分工准备没有重新执行841项；运行源码不变。详细记录见[MS-I2g准备](MS-I2g-preparation.md)、[项目实际进度](PROGRESS-2026-10-08.md)及[完整功能包](../coordination/requests/A/MS-I2g-parallel-packages.md)。
