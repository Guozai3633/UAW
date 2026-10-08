# 全局文档作用与位置

状态：2026-10-07。入口是[项目README](../README.md)。**产品约束 → 总体职责 → 详细策略/接口 → 技术组件与分轮计划 → 实现/测试证据**分层维护；P0工程/开发存储已开始实现，业务能力仍按实际验收记录判断。

## 1. 权威与阅读顺序

| 层级/位置 | 作用 | 谁维护、怎样更新 |
| --- | --- | --- |
| [ARCHITECTURE.md](../ARCHITECTURE.md) | 当前产品决策、Runtime边界与版本变更 | 人工审阅；用户纠正优先，不由生成器改产品方向 |
| [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) | 代码目录、依赖与分阶段开发 | 人工维护；路径变更同时修设计映射 |
| [TECHNOLOGY_STACK.md](../TECHNOLOGY_STACK.md) | 各模块技术主选及整体连接 | 人工维护；技术适配不能改用户目标/模型/权限 |
| [technology/README.md](technology/README.md) | 逐模块技术组件、子节点与轮次 | 从technology/catalog.py生成；安装/验证范围关联实施记录 |
| [technology/FRAMEWORK_BOUNDARIES.md](technology/FRAMEWORK_BOUNDARIES.md) | LangGraph/LangChain/UAW状态与执行分工 | 人工维护；局部图、任务图和职责图分开 |
| [technology/DATA_AND_DEPLOYMENT.md](technology/DATA_AND_DEPLOYMENT.md) | 数据权威、事务/待办、向量、缓存、部署profile | 人工维护；D01部署权威仍待用户确认 |
| [technology/DEPENDENCIES.md](technology/DEPENDENCIES.md) | 包/服务、依赖组、采用阶段与冻结方式 | 生成；设计基线不是实际安装锁 |
| [technology/VALIDATION.md](technology/VALIDATION.md) | 框架接入及各轮兼容验证门槛 | 人工维护；真实回执存实施报告 |
| [technology/COVERAGE.md](technology/COVERAGE.md) | 115节点→组件→目录→设计→接口→开发轮 | 生成；覆盖不代表运行能力 |
| [technology/catalog.py](../technology/catalog.py) | 技术主选与子节点绑定源 | 人工维护；组件更换同步边界/验证与计划 |
| [technology/node-map.json](../technology/node-map.json) | 节点的技术落点机器映射 | 生成；implemented=false，供定位与检查 |
| [DEVELOPMENT_PLAN.md](../DEVELOPMENT_PLAN.md) | 开发计划总览与第一轮入口 | 人工维护；说明实施顺序，不自行改产品约束 |
| [plan/README.md](plan/README.md) | 模块→阶段→50轮独立工作包 | 从planning/catalog.py生成；每轮任务/目录/验收完整列出 |
| [plan/SEQUENCE.md](plan/SEQUENCE.md) | 全局依赖、阶段门槛和可并行开发部分 | 生成；模块分组不等于依次写完模块 |
| [plan/DECISIONS.md](plan/DECISIONS.md) | 技术主选待验证项、产品/部署待定项与最晚轮 | 生成；技术主选见技术栈，实际权威/供应商/范围另行确定 |
| [plan/COVERAGE.md](plan/COVERAGE.md) | 节点到实施轮、详细设计、接口、代码目标 | 生成；计划覆盖不是实现覆盖 |
| [plan/INTERFACE_ASSIGNMENTS.md](plan/INTERFACE_ASSIGNMENTS.md) | 接口反查关联工作包 | 生成；关联轮次不等于接口已经就绪 |
| [planning/catalog.py](../planning/catalog.py) | 开发任务/门槛/依赖/范围的唯一计划源 | 人工维护；调整计划后重建，实际验收需附证据 |
| [planning/plan-map.json](../planning/plan-map.json) | 节点到开发轮次的机器映射 | 生成；不产生implemented=true |
| [plan/ROUND_TEMPLATE.md](plan/ROUND_TEMPLATE.md) | 每轮实际执行与验收报告模板 | 复制到实施目录，记录实际代码/初态/回执/未过项 |
| [plan/PARALLEL.md](plan/PARALLEL.md) | 3/4/5个session配置、独立子包与当前开工条件 | planning/parallel_catalog.py维护；总计划生成器同时重建 |
| [plan/PARALLEL_WORKFLOW.md](plan/PARALLEL_WORKFLOW.md) | Git基线、目录隔离、公共变更、合并及组合验证 | 人工维护；集成session执行后附实际SHA和回执 |
| [plan/sessions/A.md](plan/sessions/A.md)、[B](plan/sessions/B.md)、[C](plan/sessions/C.md)、[D](plan/sessions/D.md)、[E](plan/sessions/E.md) | 每个session任务/允许目录及可复制开工说明 | 由并行计划源生成；文档存在不代表已创建聊天或派发 |
| [coordination/HANDOFF_TEMPLATE.md](coordination/HANDOFF_TEMPLATE.md)、[REQUEST_TEMPLATE](coordination/REQUEST_TEMPLATE.md) | 工作包交接与公共接口提案 | 开发session填写各自文件；A记录派发与集成决定 |
| [implementation/README.md](implementation/README.md) | 实际代码范围、启动/检查及未完成能力 | 人工维护；对应真实回执与冻结版本 |
| [implementation/P0-05.md](implementation/P0-05.md) | 模型网关/固定政策/协议/用量实际范围与未过项 | 人工维护；协议fixture不替代实际LLM验收 |
| [implementation/P1-01.md](implementation/P1-01.md) | 本轮写入代码、未完成验证和A收尾清单 | 当前部分实现记录，不是验收通过报告 |
| [implementation/MS-I1.md](implementation/MS-I1.md)、[A接线说明](coordination/requests/A/MS-I1-adapters.md) | 三份组件接受、真实Context接线、消费边界与下一包 | 222项回归通过；通用build/真实配对与执行仍未验收 |
| [implementation/MS-I2a.md](implementation/MS-I2a.md)、[公共消费协议](coordination/requests/A/MS-I2a-ports.md) | 人工审批持久化、真实签名原语和C/D后续子包 | 原251项通过；实际工具执行、配对/IPC仍待接线 |
| [implementation/MS-C2-acceptance.md](implementation/MS-C2-acceptance.md)、[A接收决定](coordination/requests/A/MS-C2-integration.md) | 固定快照/引用组件接受、真实SQL与生产适配器缺口 | 当时285项通过；P1-02仍开发中，MS-C3已接受，B暂无新包 |
| [implementation/MS-I2b.md](implementation/MS-I2b.md)、[权限接口说明](coordination/requests/A/MS-I2b-permissions.md) | Context/Model/Approval统一实时父子权限、当前撤销和模型停止 | 当时300项通过；不代表工具/Runner执行已就绪 |
| [coordination/DISPATCH.md](coordination/DISPATCH.md)、[转发消息](coordination/NEXT_WAVE.md) | 当前基线、接受范围和各session开工状态 | A维护；没有代替worker切换分支或发送消息 |
| [implementation/MODEL_CONNECTION.md](implementation/MODEL_CONNECTION.md) | 批准提供方profile、私有凭据及实连CLI | 按实际提供方配置执行，回执保存在私有.data |
| [implementation/CONTROL_PLANE.md](implementation/CONTROL_PLANE.md) | 开发用户/管理员认证、配置发布与任务受理操作 | 仅本机开发入口；不声称公网登录或模型已连通 |
| [implementation/P0-03.md](implementation/P0-03.md)、[P0-04](implementation/P0-04.md) | 配置、原文、状态、事件及账本的实际策略/验收 | 独立于目标设计；本轮限制与证据在此记录 |
| [contracts/implementation_catalog.py](../contracts/implementation_catalog.py) | 已实现接口的代码入口与明确范围 | 手工核对后维护；不按文件存在自动置True |
| [implementation/evidence/environment.json](implementation/evidence/environment.json) | 实际核心版本、源码Hash和检查范围 | 检查通过后采集，不记录环境变量或秘密 |
| `docs/decisions/`、`docs/implementation/` | 实际选型和真实开发报告 | 按每轮结果更新，未实施部分不标已验收 |
| [COMMON_CONTRACTS.md](design/COMMON_CONTRACTS.md) | 所有组件共同的请求/结果/状态/失败规则 | 人工维护；子策略只能收窄和具体化 |
| [api/README.md](api/README.md) | 五类接口分类入口、调用链、覆盖和机器文件 | 从契约源生成；不声称后端已实现 |
| [api/CONVENTIONS.md](api/CONVENTIONS.md) | 字段单位、信任边界、HTTP/结果、幂等/CAS、分页/SSE、审批/恢复 | 人工维护；与schema和策略同步 |
| [api/OBJECTS.md](api/OBJECTS.md) | 每个对象、请求、返回及互斥分支的字段页 | 从interface_catalog.py生成；自动DTO不是数据库表 |
| [api/COVERAGE.md](api/COVERAGE.md) | 架构节点→接口→详细策略→计划代码 | 生成；共享设施根只汇总子设施接口 |
| [interface_catalog.py](../contracts/interface_catalog.py) | 对象/操作/硬结构约束的唯一契约源 | 人工维护；重建OpenAPI、工具目录和字段文档 |
| [uaw.schema.json](../contracts/uaw.schema.json) | 统一JSON Schema对象定义 | 生成；不能手改产生另一套字段 |
| [openapi.json](../contracts/openapi.json) | HTTP方法、路径、参数位置、认证、响应 | 生成；目前仅设计，非已部署服务 |
| [SUBAGENT_LIFECYCLE.md](design/SUBAGENT_LIFECYCLE.md) | 创建/发现/调用/验收完整链路 | 人工维护；与提示词、控制工具、定义schema对齐 |
| [design/README.md](design/README.md) | 全部架构节点的文档与代码定位 | 生成；每个当前图节点各有独立策略文档，数量以覆盖检查为准 |
| `docs/design/modules/*.md` | 每个大模块的内部组织、数据/接口/策略/门槛 | 从 [catalog.py](../design/catalog.py) 生成 |
| `docs/design/components/*.md` | 细分节点的具体字段、处理顺序、提交/错误/缓存与验收 | 从catalog生成；不是只复制功能描述 |
| [ARCHITECTURE_ATLAS.md](../ARCHITECTURE_ATLAS.md) | 分层节点及其调用/数据/状态/政策联系 | 从 [build_atlas.py](../architecture/build_atlas.py) 生成 |
| [graph.json](../architecture/graph.json) | 可消费的节点/关系和开发文档链接 | 图生成产物；不能直接编辑后忘记维护源 |
| [design-map.json](../design/design-map.json) | 节点ID→文档→计划代码、implemented=false | 设计生成产物；用于覆盖检查与图谱跳转 |

遇到冲突先核对用户明确要求与主架构，再更新详细策略维护源/目录与关系图，最后重建生成文档。生成覆盖检查只证明每个节点有设计，不证明策略正确、第三方API可用或Runtime已实现。

## 2. 专项文档

| 位置 | 作用 |
| --- | --- |
| [RUNTIME_DECISIONS.md](../RUNTIME_DECISIONS.md) | 模型继承、会话定义、撤销与历史决策 |
| [CONTROL_TOOLS.md](../CONTROL_TOOLS.md) | 主Agent可调用的控制工具及所属Runtime |
| [CACHE_DESIGN.md](../CACHE_DESIGN.md) | 多层复用、key/权限/时效依赖、有效命中与成本 |
| [DELIVERY_VERIFICATION.md](../DELIVERY_VERIFICATION.md) | 真实完成、交付物、引用与代码验证 |
| [LOCAL_APPROVAL_SEMANTIC.md](../LOCAL_APPROVAL_SEMANTIC.md) | 本地项目、三审批模式、语义判断边界 |
| [ADMIN_CONFIGURATION.md](../ADMIN_CONFIGURATION.md) | 模型/搜索/API由管理员配置、凭据及私人授权 |
| [ENGINEERING_COMPLETENESS.md](../ENGINEERING_COMPLETENESS.md) | 观测/评测、生命周期、MCP、资源/恢复的跨模块边界 |
| [ACADEMIC_AGENT.md](../ACADEMIC_AGENT.md) | 学术角色的证据、假设、推导与复现要求 |
| [FRONTEND_BLUEPRINT.md](../FRONTEND_BLUEPRINT.md) | 日常用户页面信息架构与交互 |
| [PRODUCT_VALIDATION.md](../PRODUCT_VALIDATION.md) | 首批任务、接受/返工/成本/持续使用验证 |
| [NOTION_ARCHITECTURE_REVIEW.md](../NOTION_ARCHITECTURE_REVIEW.md) | 11专题的来源、阅读范围及架构落点 |
| [CRITICAL_REVIEW_2026-10-02.md](../CRITICAL_REVIEW_2026-10-02.md) | 当时版本的架构/市场评审；是历史判断，不自动覆盖后续主架构 |
| `research/2026-10-03-deep-v1/` | 市场/跨行业研究、证据与待验证假设 |

专项文档解释一类跨模块问题；节点详细文档指导具体组件实现。二者不能独立维护相反权限/模型政策。存在尚未确认项（如三模式文案含义、历史权威位置）保持明确待定。

## 3. 提示词与页面

| 位置 | 作用 |
| --- | --- |
| [main_agent.md](../prompts/main_agent.md) | 精炼常驻主Agent规则 |
| [agent_definition.md](../prompts/agent_definition.md) | 按需加载的子Agent设计方法 |
| [subagent_invocation.md](../prompts/subagent_invocation.md) | 按需发现、选择、委派和验收原则 |
| [execution_assessment.current.md](../prompts/execution_assessment.current.md) | 当前规划/委派/并发评估，与统一schema对齐 |
| [execution_assessment.md](../prompts/execution_assessment.md) | 早期实验模板，仅对照，不用于当前字段校验 |
| [semantic_verification.md](../prompts/semantic_verification.md) | 语义目标与真实证据核对 |
| [execution_assessment.schema.json](../contracts/execution_assessment.schema.json) | 当前统一ExecutionAssessment的引用入口；旧实验存legacy/ |
| [uaw-workspace.html](../demo/uaw-workspace.html) | 聊天与工作区模拟蓝图，不访问实际项目 |
| [uaw-architecture-map.html](../demo/uaw-architecture-map.html) | 设计讨论图谱，节点可跳详细开发文档 |

## 4. 维护清单

- 改用户行为：同步主架构、相关专项、提示词和具体组件策略。
- 改节点关系：修改architecture维护源，节点增删必须补策略catalog与目录映射。
- 改策略：修改design/catalog.py，重建设计文档，再重建图谱。
- 改字段/接口：修改contracts/interface_catalog.py，生成接口/对象/OpenAPI，运行契约校验，再重建设计与图谱；权限/效果等语义闸门要同时修策略。
- 改开发任务/阶段/依赖：修改planning/catalog.py并运行planning/build_plan.py；新节点要安排实施轮，相关接口会从统一映射关联。计划不覆盖设计策略或准确字段定义。
- 改技术组件：修改technology/catalog.py及必要跨模块说明，重建technology/build_stack.py；补实际兼容门槛并同步计划。不能把主选设计改写成已运行证据。
- 改代码路径：更新目录说明与设计生成器映射，不能制造指向不存在实现的“已实现”标识。
- 真正开发后：实现与验收记录另存，逐节点填入真实证据，不能只把implemented布尔值改为true。

## 最新集成与派发

- [MS-I2c接受记录](implementation/MS-I2c.md)：C/D组件及预算恢复接口，360项全量检查。
- [MS-I2c消费契约](coordination/requests/A/MS-I2c-ports.md)：BudgetState、ToolReceipt、AsyncRunnerAuthority和ModelPrompt边界。
- [直接转发到B/C/D的消息](coordination/NEXT_WAVE.md)：MS-C3/MS-T2b/MS-R2b，统一ms-i2c。

## MS-I2d最新接续

- [本轮接受记录](implementation/MS-I2d.md)：MS-C3/MS-R2b和A根执行租约、Model输入路由；完整MS-I2仍开发中。
- [消费接口](coordination/requests/A/MS-I2d-ports.md)：ExecutionLeasePort/CAS/fence/期限/清理与真实命名空间路由。
- B/D保留交付边界，C继续ms-i2c/MS-T2b；当前安排见[派发表](coordination/DISPATCH.md)。
