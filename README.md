# UAW 项目全局指引

UAW 面向办公、开发与学术任务，采用 Python 构建可扩展 Agent Runtime。**P0-01工程基础、P0-03管理配置和P0-04任务受理/资源账本已完成开发验证；P0-05模型网关与协议已实现，真实LLM验收待提供方配置；P0-02开发存储已验证，最终部署D01待定。Agent循环、工具执行、Runner和实际前端尚未接入。**

[开发启动与实际进度](docs/implementation/README.md)：`./ops/start.ps1 -WithPostgres`启动本机开发后端，`./ops/check.ps1 -WithPostgres`运行真实数据库检查。

P1-01任务理解协议已实现，当前全量73项检查通过；真实模型语义质量仍待验收。Git远端已关联[项目仓库](https://github.com/Guozai3633/UAW)，集成分支为`integration`。采用 **3个开发session＋1个集成session**；B/C/D独立分支、worktree和环境已准备，开发聊天待在对应目录开启，实际基线及派发状态见[统一记录](docs/coordination/DISPATCH.md)：[分工计划](docs/plan/PARALLEL.md) · [开工和合并](docs/plan/PARALLEL_WORKFLOW.md)。

## 先看这些入口

| 文档 | 用途 |
| --- | --- |
| [主架构](ARCHITECTURE.md) | 已确认产品约束、七个 Runtime 的职责与版本变化 |
| [实际实现与启动](docs/implementation/README.md) | 当前代码范围、启动/检查命令、真实回执及未完成能力 |
| [技术栈总览](TECHNOLOGY_STACK.md) | 各模块的技术主选、框架分工、数据与部署边界 |
| [逐模块技术组件](docs/technology/README.md) | 13个技术分组及115个子节点的组件/目录/轮次对应 |
| [开发计划总览](DEVELOPMENT_PLAN.md) | 模块→阶段→每轮任务；目标、依赖、目录、交付物与验收 |
| [逐模块开发计划](docs/plan/README.md) | 11个职责分组、六阶段、50轮独立工作包 |
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

继续建设：七Runtime的业务能力、`apps/web/`前端、`apps/local_runner/`本地执行器。设计索引中的代码目标不等于全部已实现，未接入能力仍报告不可用。

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
