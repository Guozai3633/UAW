# 当前实现与开发启动

2026-10-08：P0-01工程基础、P0-03开发管理配置、P0-04受理/事件/资源账本已验证。P0-05模型网关与协议已实现并测试，尚无真实LLM验收回执。P0-02开发持久化已验证，最终D01尚未确认。Agent任务循环、工具执行、Runner和实际Web应用尚未接入。

当前全量 **563 项通过，无失败/错误/跳过**；使用真实 PostgreSQL、本机临时路径、受控模型响应和真实 Ed25519 原语，实际 LLM/配对/Runner 执行仍未验收。MS-I1 完成理解接线，MS-I2a 完成人工审批和签名公共基础，B 的 MS-C2 快照/引用组件已接受，MS-I2b 将 Context/Model/Approval 接入同一实时父子权限服务。MS-T2a/MS-R2a 组件已接受，MS-I2c 补齐预算恢复读与下一轮消费契约。B/C/D 的 MS-C3/MS-T2b/MS-R2b 已接受；MS-I2d 的根执行租约和输入路由、MS-I2e 的 Tool 核对集成已验证。下一包统一 ms-i2e，B/C/D 执行 MS-C4/MS-T2c/MS-R2c，A继续 MS-I2f 设备/命令权威接线。见 [MS-I1](MS-I1.md)、[MS-I2a](MS-I2a.md)、[MS-C2 接受记录](MS-C2-acceptance.md)、[MS-I2b](MS-I2b.md)、[MS-I2c](MS-I2c.md)、[MS-I2d](MS-I2d.md)、[MS-I2e](MS-I2e.md)、[统一派发表](../coordination/DISPATCH.md)及[并行计划](../plan/PARALLEL.md)。

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
