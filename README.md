# UAW 项目全局指引

UAW面向办公、开发与学术任务，采用Python构建可扩展Agent Runtime。当前H02-v7已接通普通交流、同Run澄清/纠正、单Agent文本成果、审阅等待暂停与接受。原账号/历史沿用，实际页面可测试；本人体验、独立事实质量和完整本机文件链仍待验收。

2026-10-18实际版本：后端d2000f9、前端B af3889f，见[本人测试清单](docs/implementation/human-tests/H02-v7.md)和[A16全部回执](docs/implementation/evidence/h02-i04-a16.json)。50不同SQL最终通过，真实固定模型样例与所有18调用/失败/pending费用保留；不能据此宣称全任务质量达标。原超时任务保持失败，报告只读保留。

架构v0.11采纳已确认Q1–Q8：[确认决策](docs/decisions/ADR-001-conversation-and-delivery.md)、[执行详细设计](docs/design/CONVERSATION_EXECUTION.md)、[H02安排](docs/plan/H02_CONVERSATION.md)。[公共契约](docs/coordination/requests/A/H02-P1-12-ports.md)与[A16内部审阅等待约束](docs/coordination/requests/A/H02-I04-A16-review-wait-contract.md)分别记录结构和实际装配。

仓库为[Guozai3633/UAW](https://github.com/Guozai3633/UAW)，集成分支integration。实际源码、会话交付与开工版本以[DISPATCH](docs/coordination/DISPATCH.md)页首为准；本次没有新worker正式基线，B/C/D保留原提交。旧MS-I2i的1691全量及原失败保留，不能覆盖后续设计。

[开发启动与实际能力](docs/implementation/README.md) · [当前问题修复](docs/implementation/human-tests/H02-I04.md) · [历史本人反馈](docs/implementation/human-tests/H01-I02.md)。管理员凭据仍走受保护配置，不进入文档或模型。

## 先看这些入口

下一步先按[体验清单](docs/implementation/human-tests/H02-v7.md)收集本人反馈，并完成人工事实样本核对。当前续项由A独立完成，BCD停在原交付点；后续按[H02计划](docs/plan/H02_CONVERSATION.md)和正式DISPATCH安排，不自动同步或扩包。本机与协作验收独立推进。

| 文档 | 用途 |
| --- | --- |
| [主架构](ARCHITECTURE.md) | 已确认产品约束、七个 Runtime 的职责与版本变化 |
| [实际实现与启动](docs/implementation/README.md) | 当前代码范围、启动/检查命令、真实回执及未完成能力 |
| [技术栈总览](TECHNOLOGY_STACK.md) | 各模块的技术主选、框架分工、数据与部署边界 |
| [逐模块技术组件](docs/technology/README.md) | 13个技术分组及115个子节点的组件/目录/轮次对应 |
| [开发计划总览](DEVELOPMENT_PLAN.md) | 模块→阶段→每轮任务；目标、依赖、目录、交付物与验收 |
| [逐模块开发计划](docs/plan/README.md) | 11个职责分组、六阶段、56轮独立工作包 |
| [多session并行计划](docs/plan/PARALLEL.md) | 独立子包、各session修改目录、依赖、交接与合并流程 |
| [项目目录设计](docs/PROJECT_STRUCTURE.md) | 功能模块落在哪个代码目录、模块怎样互相依赖 |
| [子智能体完整设计](docs/design/SUBAGENT_LIFECYCLE.md) | 主 Agent 如何设计/创建角色、何时调用、如何隔离和验收 |
| [开发设计总索引](docs/design/README.md) | 每个架构节点 → 独立策略文档 → 计划代码位置 |
| [功能接口总入口](docs/api/README.md) | HTTP、模型工具、Runner、Runtime和内部组件的输入/输出/约束 |
| [对象总字典](docs/api/OBJECTS.md) | 全部对象、字段、必填性、枚举、单位、分支和示例 |

## 看图进入细节

[打开分层交互图](demo/uaw-architecture-map.html)：总体 → 模块内部 → 关键链路。点击节点后可进入对应开发设计。

[文字图谱](ARCHITECTURE_ATLAS.md) 便于审阅关系；[文档作用地图](docs/DOCUMENT_MAP.md) 解释每份文档的作用、位置和维护权威。先读具体负责的模块及其子节点，不必一次读完全部文档。

## 开发前必须保留的规则

- 用户原文是基准；预览只提醒系统的理解。
- 默认单 Agent，规划、委派与并行分别按语义和真实资源决定。
- 用户选定模型由根/子实例继承，仅用户明确子模型覆盖；不可用不暗换。
- 控制动作作为工具入口，业务状态由对应 Runtime 唯一负责。
- 本地项目经授权 Runner 执行；审批模式不会扩大真实权限。
- 完成核验基于真实成果/证据/版本，用户接受与AI判断分开。

## 真实存在和计划建设的区别

现在存在：根目录设计文档、`docs/` 详细策略/逐字段接口/开发计划/技术组件、`prompts/` 提示词、`contracts/` 对象schema/OpenAPI/工具目录与契约生成源、`architecture/` 与 `design/` 设计生成源、`planning/` 计划源与生成器、`technology/` 技术主选与映射源、`demo/` HTML、`research/` 研究资料。

已实现的开发基础：`src/uaw/`工程入口、公共契约、存储、受保护配置、会话/Run受理、资源账本及固定模型调用网关；`tests/`必要场景与原始材料；`ops/`启动、管理员/实连客户端、迁移与检查；`pyproject.toml`及`uv.lock`。实际证据在`docs/implementation/`，接口范围逐项记录于`contracts/implementation_catalog.py`。

继续建设：七Runtime的后续业务能力、`apps/web/`对话接续等后续交互、`apps/local_runner/`本机整链和后续执行能力。设计索引中的代码目标不等于全部已实现，未接入能力仍报告不可用。

## 维护与实施

`contracts/interface_catalog.py`维护接口与对象，`design/catalog.py`维护算法策略，`architecture/build_atlas.py`维护关系。普通修改按此顺序重建，使图和策略文档链接到接口：

```powershell
python contracts/build_interfaces.py
python design/build_design.py
python architecture/build_atlas.py
python planning/build_plan.py
python technology/build_stack.py
```

细分文档是生成产物，应修改策略源后重建；跨模块公共契约、子Agent完整链路和目录规则是独立手写文档。设计发生冲突时：用户明确要求与当前主架构约束优先，再修正策略源与图，不能让生成文档自行改变已确认方向。

技术主选由technology/catalog.py维护，各模块页自动关联准确策略/接口/轮次；框架边界、数据部署和兼容验证文档人工维护。技术设计通过不表示已经安装或联测；具体稳定版本在对应实施轮锁定。

新增/修改图节点时，先运行一次图生成器更新graph.json，再补具体策略和输入/输出契约，按上述顺序生成文档及链接。契约验证使用 `python contracts/check_interfaces.py`（独立验证环境需要jsonschema）；报告见docs/api/contract-check.json。schema/示例/覆盖通过不代表后端运行测试通过。

实施先贯通一条真实任务：原文 → 主循环 → 必要工具 → 本地/允许环境 → 真实成果 → 核验/审阅，再增加第二个任务抽象共用能力。每轮从[模块计划](docs/plan/README.md)定位职责，按[全局依赖](docs/plan/SEQUENCE.md)开工；阶段门槛以真实成果验收。实际记录在实施时写入docs/implementation/，尚未开始的轮不能标为完成。
