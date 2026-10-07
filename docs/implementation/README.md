# 当前实现与开发启动

2026-10-07：P0-01工程基础、P0-03开发管理配置、P0-04受理/事件/资源账本已验证。P0-05模型网关与协议已实现并测试，尚无真实LLM验收回执。P0-02开发持久化已验证，最终D01尚未确认。Agent任务循环、工具执行、Runner和实际Web应用尚未接入。

P1-01任务理解协议及认证frame读取已通过回归，详情见[实现范围与未过项](P1-01.md)。当前全量73项检查通过，无跳过；使用真实PostgreSQL及受控模型响应，真实模型语义质量仍待D06。Git已关联用户提供的新仓库；共同提交与多session开工状态见[统一派发表](../coordination/DISPATCH.md)及[并行计划](../plan/PARALLEL.md)。

## 已实现的代码

- Python 3.14项目、uv.lock、FastAPI启动/关闭及真实HTTP健康检查。
- 源码包和wheel已经实际构建；分发包包含运行所需的权威schema副本。
- 公共ID/Ref/Failure/Principal/Scope/RequestMeta/可信上下文子集；复用权威JSON Schema并严格处理未知字段、格式、重复键和非JSON数值。
- 七Runtime的注入port与未实现能力状态；不会给模型注册空实现工具。
- PostgreSQL迁移、主体分区、CAS、请求去重、不可变修订及逻辑删除。
- 同域数据与Outbox事务提交、SQL消费者回执去重。
- 私有不可变blob的主体分区、大小/摘要验证和并发写入。
- 开发 bearer 用户/管理员身份、Windows 凭据库存取、配置校验发布与当前撤销闸门。
- 20个开发HTTP入口和Run公共创建入口；原文、模型选择来源、任务、根预算、交互项与事件事务受理。
- 每attempt预算准入、调用意图、未知用量保留、失败结算及去重核对。
- ModelRuntime.generate与显式Chat Completions adapter；固定模型/能力复核、长输出Blob、结构输出校验、有限重试、取消和未知费用记账。实际LLM调用需要管理员批准配置。
- IntentRuntime.understand/revise与当前frame读取；保留完整用户原文、逐字来源和理解历史，新输入/取消/期限/CAS阻止旧提案提交。旧Run不静默补来源。

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

补齐D06提供方/模型/私有凭据与真实调用回执，完成P0-05及Intent语义验收；并行建设Context、Tool和Runner独立组件，随后接Agent闭环。办公、学术和代码样例在后续真实任务阶段验收。组件基线通过不代表已经通过P0真实模型门槛。
