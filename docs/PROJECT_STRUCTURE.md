# 项目功能模块与目录设计

状态：v0.10，2026-10-07。Python Runtime职责目录不变；技术主选见[技术栈](../TECHNOLOGY_STACK.md)。P0工程、开发存储、管理配置和Run受理/资源账本已有实际代码，见[实施记录](implementation/README.md)；以下是完整目标目录，未实施部分仍是计划。

## 当前实现位置

- `api/application.py、authentication.py、routes.py、documentation.py`：HTTP启动、可信身份、19个开发接口及对应OpenAPI。
- `shared/configuration.py、settings.py、credentials.py`：版本化平台配置、开发部署配置和私有凭据port；Windows实现位于 `infrastructure/credentials.py`。
- `run/facade.py、history.py、state.py、events.py、budget.py`：原文与模型选择受理、运行/交互项状态、有序事件和attempt账本。
- `model/facade.py、gateway.py、policy.py、capability.py、adapters.py、contracts.py、ports.py`：固定模型调用、协议能力、持久发送与provider适配；`context/seed.py`仅提供诊断快照，完整Context仍待实现。
- `ops/model_probe.py`：批准配置下的显式模型诊断，操作说明位于 `docs/implementation/MODEL_CONNECTION.md`。
- `infrastructure/db/transactions.py、records.py、models.py` 与 `ops/migrations/`：事务、CAS、版本记录、去重和数据库结构。
- `contracts/implementation_catalog.py`：逐接口登记实际实现范围；代码与JUnit摘要位于 `docs/implementation/evidence/`。

实际代码按已实现职责拆分，不先生成目标目录中的空实现；业务执行器尚未接入。启动与管理员操作见[开发控制层说明](implementation/CONTROL_PLANE.md)。

## 1. 目录按职责组织

多session开发的目录归属见[并行分工](plan/PARALLEL.md)，开工和合并见[流程说明](plan/PARALLEL_WORKFLOW.md)。`.worktrees/`是待Git基线完成后使用的忽略目录，不是产品Workspace Runtime；各worktree只修改自己session的允许路径。公共契约、组装根、迁移及依赖锁由集成session集中维护。

```text
UAW/
├─ README.md                         # 全局入口：先读什么、实现到哪里
├─ ARCHITECTURE.md                   # 产品约束与总体职责权威
├─ ARCHITECTURE_ATLAS.md             # 生成的分层关系图
├─ DEVELOPMENT_PLAN.md              # 开发顺序总览与第一轮入口
├─ TECHNOLOGY_STACK.md              # 各模块技术主选与框架分工
├─ docs/
│  ├─ DOCUMENT_MAP.md                # 文档作用与位置
│  ├─ PROJECT_STRUCTURE.md           # 本文：目录与依赖规则
│  ├─ technology/
│  │  ├─ README.md, DEPENDENCIES.md, COVERAGE.md, SOURCES.md
│  │  ├─ FRAMEWORK_BOUNDARIES.md, DATA_AND_DEPLOYMENT.md, VALIDATION.md
│  │  └─ modules/, technology-check.json # 各模块技术/接入/目录/轮次
│  ├─ api/
│  │  ├─ README.md, CONVENTIONS.md, FLOWS.md
│  │  ├─ HTTP.md, TOOL.md, RUNNER.md, RUNTIME.md, COMPONENT.md
│  │  ├─ OBJECTS.md, COVERAGE.md, contract-check.json
│  │  └─ interfaces/, objects/, nodes/ # 逐接口/对象字段/节点入口
│  ├─ plan/
│  │  ├─ README.md, STAGES.md, SEQUENCE.md, DECISIONS.md
│  │  ├─ COVERAGE.md, INTERFACE_ASSIGNMENTS.md, STATUS.md
│  │  ├─ ROUND_TEMPLATE.md, plan-check.json
│  │  └─ modules/, rounds/           # 模块→阶段→每轮目标/任务/目录/验收
│  └─ design/
│     ├─ README.md                   # 图节点→策略文档→代码目标
│     ├─ COMMON_CONTRACTS.md         # 请求、结果、权限、状态与恢复
│     ├─ SUBAGENT_LIFECYCLE.md        # 创建/发现/调用的完整行为
│     ├─ modules/                    # 七Runtime + 共享支撑层设计
│     └─ components/                 # 每个细分节点的独立开发策略
├─ architecture/                    # 关系维护源、图JSON、HTML模板
├─ design/                          # 详细策略维护源与设计映射生成器
├─ planning/                        # 任务/依赖维护源与计划生成器
│  └─ catalog.py, build_plan.py, plan.json, plan-map.json
├─ technology/                      # 技术组件与节点绑定维护源
│  └─ catalog.py, build_stack.py, components.json, node-map.json
├─ prompts/                         # 精炼行为方法，不放所有实现细节
├─ contracts/
│  ├─ interface_catalog.py          # 人工维护对象/接口/结构约束
│  ├─ build_interfaces.py, check_interfaces.py
│  ├─ uaw.schema.json, openapi.json, tools.json
│  ├─ interfaces.json, interface-map.json, examples.json
│  └─ legacy/                       # 已弃用的实验契约，仅用于迁移
├─ demo/                            # 可直接打开的模拟页面/架构图
├─ research/                        # 机会、市场和用户验证材料
│
├─ capabilities/builtin/            # 下方开始均为计划实现
│  └─ office_report/, academic_discussion/ # UAW自有技能/模板能力包
├─ src/uaw/
│  ├─ composition.py                # 唯一组装根：依赖注入和模块接线
│  ├─ application.py                # 启动/关闭、配置/恢复入口
│  ├─ infrastructure/               # 组件adapter，不管理任务业务事实
│  │  └─ db/, blob/, http/, identity/, secrets/, telemetry/
│  ├─ api/
│  │  ├─ ingress.py                 # 身份/限额/资源/原文/Run受理
│  │  ├─ streaming.py               # Item/Event流，cursor/快照
│  │  └─ admin.py                   # 管理端API，不给普通Agent工具
│  ├─ intent/
│  │  ├─ facade.py, contracts.py, ports.py, repository.py
│  │  └─ preview.py, original.py, semantic.py, references.py,
│  │     probe.py, ambiguity.py, frame.py
│  ├─ agent/
│  │  ├─ facade.py, contracts.py, ports.py, repository.py
│  │  ├─ definitions/               # 持久定义：不等于运行实例
│  │  │  ├─ facade.py, contracts.py, ports.py, repository.py
│  │  │  └─ designer.py, validator.py, discovery.py,
│  │  │     model_intent.py, change_service.py
│  │  ├─ factory.py                 # 唯一实例工厂
│  │  ├─ engines/                   # AgentEnginePort与LangGraph封装
│  │  ├─ loop.py, assessment.py, planning.py, scheduler.py,
│  │  │  skills.py, board.py
│  │  ├─ collaboration/
│  │  │  ├─ facade.py, contracts.py, ports.py
│  │  │  └─ contract.py, instance.py, channel.py, join.py,
│  │  │     handoff.py, cancel.py
│  │  └─ completion/
│  │     ├─ facade.py, contracts.py, ports.py
│  │     └─ contract.py, evidence.py, semantic.py, version.py,
│  │        delivery.py, acceptance.py
│  ├─ context/
│  │  ├─ facade.py, contracts.py, ports.py, repository.py
│  │  ├─ sources.py, rules.py, ingestion.py, retrieval.py,
│  │  │  selection.py, compression.py, composer.py, references.py
│  │  └─ memory/
│  │     ├─ facade.py, contracts.py, ports.py
│  │     └─ candidate.py, policy.py, conflict.py, store.py, forget.py
│  ├─ tool/
│  │  ├─ facade.py, contracts.py, ports.py, repository.py
│  │  ├─ registry.py, discovery.py, effects.py, failure.py,
│  │  │  adapters.py, results.py, audit.py
│  │  ├─ invocation/
│  │  │  ├─ facade.py, contracts.py, ports.py
│  │  │  └─ schema.py, precheck.py, approval.py, recheck.py,
│  │  │     dispatch.py, result.py
│  │  ├─ mcp/
│  │  │  ├─ facade.py, contracts.py, ports.py
│  │  │  └─ provider.py, session.py, capabilities.py,
│  │  │     invoke.py, invalidate.py
│  │  └─ control/                  # 统一控制工具→所属facade适配
│  │     └─ agents.py, context.py, tasks.py, workspace.py,
│  │        interaction.py, models.py
│  ├─ workspace/
│  │  ├─ facade.py, contracts.py, ports.py, repository.py
│  │  ├─ binding.py, base.py, isolation.py, environment.py,
│  │  │  process.py, changes.py, artifacts.py, review.py
│  │  └─ backends/                 # 同一工作区协议，真实隔离差异保留
│  │     └─ local.py, cloud.py, snapshot.py, formats.py
│  ├─ model/
│  │  ├─ facade.py, contracts.py, ports.py, repository.py
│  │  └─ catalog.py, policy.py, capability.py, gateway.py,
│  │     adapters.py, recovery.py, usage.py
│  ├─ run/
│  │  ├─ facade.py, contracts.py, ports.py, repository.py
│  │  ├─ runner_devices.py, runner_commands.py, runner_authority.py # 已实现控制服务组件，真实执行来源未接
│  │  ├─ history.py, state.py, events.py, budget.py,
│  │  │  approval.py, checkpoint.py, cancel.py, trigger.py
│  │  └─ resume/
│  │     ├─ facade.py, contracts.py, ports.py
│  │     └─ lease.py, versions.py, access.py, effects.py,
│  │        workspace.py, continue_run.py
│  └─ shared/
│     ├─ contracts.py               # Ref/Failure/Scope/ExecutionContext
│     ├─ configuration.py, extensions.py, cache.py,
│     │  observability.py, evaluation.py, stores.py
│     └─ __init__.py                # 各独立支撑入口，不造万能Runtime
├─ apps/
│  ├─ web/src/features/             # React/TypeScript/Vite技术主选，待实现
│  │  └─ workspace/, chat/, agent_definitions/, review/,
│  │     references/, approvals/, run_controls/, admin/
│  └─ local_runner/uaw_runner/
│     ├─ application.py, pairing.py, protocol.py
│     └─ scope_guard.py, filesystem.py, process_executor.py,
│        environment.py, snapshots.py, leases.py
├─ tests/
│  ├─ unit/<runtime>/               # 具体状态/算法/范围规则
│  ├─ integration/                  # create/invoke/approval/recovery等边界
│  ├─ fixtures/                     # 原始材料、初态、工具模拟
│  └─ evaluation/                   # 真实任务的版本回归，隐藏集受限
└─ ops/                             # 实施时的配置模板/启动/迁移/观测
```

`run.resume.continue` 是稳定架构节点ID，计划代码文件实际使用 `continue_run.py`，避免Python关键字；节点ID不用为了代码文件名改变。目录树中同一行列多个文件是职责示意，不表示已生成文件。

## 2. 大模块和子包什么时候划分

大模块有facade/contracts/ports，保存该领域全部业务入口。已有第三层细分的节点使用子包，其他叶子先用单个策略文件；复杂度增加后可以在同公共入口下进一步拆分。不是每个函数一个目录，也不先拆微服务。

定义注册是明确的子系统，因此 `agent.definitions` 使用子包；其内部文件职责由 SUBAGENT_LIFECYCLE 指定。`support` 只是共享支撑分组，各入口独立，不提供执行全部支撑模块的万能facade。

## 3. 依赖方向与调用方式

| 调用方 | 允许依赖 | 不允许的方式 |
| --- | --- | --- |
| API/Ingress | 公共契约、Run/Intent/Agent公共入口、流适配 | 改写用户问题、直接拼内部计划或执行shell |
| Agent | Context/Tool/Model/Run/Workspace的port | 写别的Runtime Repository、伪造批准 |
| Context | 获准资料/工作区Reader、Model、缓存/索引接口 | 读取任意本地目录、用摘要授予权限 |
| Tool | 所属领域facade和提供方adapter | 将发现等同授权、另存可独立批准的审批 |
| Workspace | Runner/沙箱、存储、政策/预算port | 在Runtime服务环境执行任意任务代码 |
| Model | 提供方、配置/凭据、Run预算port | 替用户固定模型、将key注入prompt |
| Run | 领域控制port、自己的权威存储、事件传输 | 在恢复时绕过Tool对账、改别的领域版本 |

运行关系有反馈环，但Python导入不应形成循环：port在依赖方定义，composition提供实现；共享基础类型不导入Runtime。内部控制工具adapter调用公共facade，facade不再递归调用同一个Tool入口创建无限循环。

## 4. 本地Runner是独立执行边界

服务Runtime发送已授权的项目/能力/版本请求，本地Runner再按本地绑定检查设备、真实路径、链接、读写/执行范围与隔离；Runner的批准与撤销必须与服务策略一致地收窄。Runtime崩溃不能让任务代码取得服务凭据。

Runner运行任务进程并管理停止/租约/日志；项目venv只隔离依赖，不能声明OS安全沙箱。可选云端backend报告实际沙箱能力。普通网页不能仅凭输入路径访问用户电脑。

## 5. 分阶段开发

实施细分以 [开发计划](../DEVELOPMENT_PLAN.md) 和 [每轮依赖](plan/SEQUENCE.md) 为准：

| 阶段 | 代码与交付重点 |
| --- | --- |
| P0 工程起步 | composition/application、最小公共类型、真实持久化/配置、Run受理与固定模型 |
| P1 单Agent闭环 | Intent/Context/Tool接线、本地Runner、文件/进程/成果、核验/人工审批/真实页面 |
| P2 角色与工作成果 | 上传/搜索、Skills、create/invoke、单子任务/Join、办公与学术样例 |
| P3 规划与并行 | steps/DAG、工具/子任务并发、隔离/合并、局部审阅/撤销、多会话冲突 |
| P4 效率与扩展 | 记忆/压缩、向量发现、缓存、MCP/能力包、环境、明确Auto授权、完整管理页面 |
| P5 恢复与试用 | 检查点/租约/对账续跑、版本评测、试用资料；默认关闭扩展与推特后续设计分别跟踪 |

每阶段都有可运行真实任务和失败验证，不以完成目录或接口数量算实现完成。代码路径索引见 [开发设计总索引](design/README.md)，产品阈值先测基线。

## 6. 开发记录与后续适配目录

- `docs/decisions/`：实际技术/部署选型与理由，实施时创建。
- `docs/implementation/<轮次>.md`：真实代码、回执、费用、验收和未过项，使用 [每轮模板](plan/ROUND_TEMPLATE.md)。P0实施记录已建立，后续按轮追加。
- `extensions/twitter/`、`docs/integrations/`：后续包装候选位置，范围确认后再设计和开发，不阻塞独立UAW。

`planning/catalog.py`只维护工作包和依赖；对象字段仍由contracts源负责，算法策略仍由design源负责。目录/节点变更时同步三者映射并重建，避免计划指向旧文件。

## 7. 技术组件补充目录

- `src/uaw/agent/engines/`：LangGraph适配与自有EnginePort；asyncio回退只有实际实现并验收后才可启用。
- `src/uaw/model/providers/`、`src/uaw/tool/providers/`：批准官方SDK/HTTP/MCP适配；策略入口仍在对应Runtime。
- `src/uaw/context/readers/`、`parsers/`、`indexes/`：资料/格式/索引adapter，不产生另一套上下文入口。
- `apps/web/src/lib/{api,events,cache}/`、`components/`：生成客户端、SSE ItemReducer、账号隔离缓存与共享控件。
- `apps/local_runner/uaw_runner/{ui,platforms}/`：PySide本机选择helper、Windows Job Objects/其他OS实现。

这些路径补充完整职责目录，不表示全部已经实现。新第三方组件接入通过port/组装根，不让FastAPI/LangGraph/ORM对象进入跨Runtime公共协议。
