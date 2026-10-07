# 技术栈与组件文档索引

[先看技术总览](../../TECHNOLOGY_STACK.md) · [全局文档地图](../DOCUMENT_MAP.md)

本轮把主选组件对应到七Runtime及API/Web/Runner/工程等配套模块。每页写组件、细分技术落点、接入/状态/替换策略、目标目录和开发轮，当前仍是技术设计。

## 按模块阅读

| 模块 | 对应节点数 | 开发位置 |
| --- | --- | --- |
| [Intent：用户问题加工](modules/intent.md) | 8 | `src/uaw/intent/`、`prompts/` |
| [Agent：主循环、角色与协作](modules/agent.md) | 29 | `src/uaw/agent/`、`src/uaw/agent/engines/` |
| [Context：资料、上下文与记忆](modules/context.md) | 15 | `src/uaw/context/`、`src/uaw/context/readers/` |
| [Tool：发现、执行与失败治理](modules/tool.md) | 21 | `src/uaw/tool/`、`src/uaw/tool/control/` |
| [Workspace：项目、环境与交付](modules/workspace.md) | 9 | `src/uaw/workspace/`、`src/uaw/workspace/backends/` |
| [Model：模型政策与实际调用](modules/model.md) | 8 | `src/uaw/model/`、`src/uaw/model/providers/` |
| [Run：历史、审批与恢复](modules/run.md) | 16 | `src/uaw/run/`、`src/uaw/run/resume/` |
| [共享设施：存储、缓存、配置与观测](modules/support.md) | 7 | `src/uaw/shared/`、`src/uaw/infrastructure/` |
| [API与账号入口](modules/api.md) | 1 | `src/uaw/api/`、`src/uaw/infrastructure/identity/` |
| [Web：聊天、成果与用户控制](modules/web.md) | 1 | `apps/web/src/features/`、`apps/web/src/lib/api/` |
| [本地Runner：设备、文件与进程](modules/runner.md) | 0 | `apps/local_runner/uaw_runner/`、`apps/local_runner/uaw_runner/ui/` |
| [工程、验证与部署](modules/engineering.md) | 0 | `src/uaw/composition.py`、`src/uaw/application.py` |
| [后续推特包装](modules/integration.md) | 0 | `extensions/twitter/`、`docs/integrations/` |

Runner/工程/后续适配是配套分组，七Runtime加共享支撑的逻辑边界不变。

## 跨模块设计

| 文档 | 回答的问题 |
| --- | --- |
| [框架职责](FRAMEWORK_BOUNDARIES.md) | LangGraph、LangChain、UAW各自管什么，三个图和父子实例怎样区分 |
| [数据/缓存/部署](DATA_AND_DEPLOYMENT.md) | 唯一权威、事务/待办、向量、缓存和云/本地profile |
| [依赖与版本](DEPENDENCIES.md) | 每个包/服务什么时候加入、怎样冻结、哪些按需 |
| [兼容与接入验证](VALIDATION.md) | 决定框架能否采用、各阶段的真实验证门槛 |
| [115节点技术对应表](COVERAGE.md) | 节点→组件→代码→策略→接口→轮次 |
| [官方资料](SOURCES.md) | 本次查阅的功能/协议资料，库能力与UAW设计分开 |
| [文档检查报告](technology-check.json) | 组件/节点/引用检查；不代表依赖兼容或Runtime通过 |

## 维护源与准确性

[组件/模块/节点主选源](../../technology/catalog.py) · [文档与映射生成器](../../technology/build_stack.py) · [机器映射](../../technology/node-map.json)

修改catalog后运行 `python technology/build_stack.py`；框架、数据与验证跨模块文档人工维护。版本采用稳定发行版并在实际开发锁定；官网latest可能展示dev文档，不把该版本直接当安装建议。

当前仍待：D01历史权威位置、具体IdP/模型/搜索/embedding/秘密/云执行提供方、首批文件范围、三审批模式最终文案、成本阈值。技术主选已给出，不等同这些产品/部署条件已经确认。

