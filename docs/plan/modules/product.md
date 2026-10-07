# API与前端 · 开发计划

[计划总索引](../README.md) · [全局顺序与并行条件](../SEQUENCE.md)

## 职责与边界

身份入口、聊天、真实状态、用户控制、审阅和管理页面。

本分组主责4轮，另关联0轮跨模块协同。按阶段逐步完善，并与其他模块轮次交替接线；协同任务引用同一个工作包，不重复计算50轮总数。七Runtime是运行职责，11个计划分组包含工程、页面和后续适配，不是11个服务。

## 阶段与工作包

### P1 · 单Agent完整闭环

| 轮次与任务 | 目标 | 直接前置 | 范围/当前状态 |
| --- | --- | --- | --- |
| [P1-10 最小API与真实聊天工作区](../rounds/P1-10.md) | 让用户从页面完成第一条任务和审阅。 | [P1-09](../rounds/P1-09.md) | 本组主责；核心开发范围 / 待开发 |

### P2 · 角色、子Agent与工作成果

| 轮次与任务 | 目标 | 直接前置 | 范围/当前状态 |
| --- | --- | --- | --- |
| [P2-08 角色与子任务页面](../rounds/P2-08.md) | 用户可查角色、修改配置并了解子任务结果。 | [P2-07](../rounds/P2-07.md)、[P1-10](../rounds/P1-10.md) | 本组主责；核心开发范围 / 待开发 |

### P4 · 上下文、缓存与能力治理

| 轮次与任务 | 目标 | 直接前置 | 范围/当前状态 |
| --- | --- | --- | --- |
| [P4-09 草稿提示、用户控制与完整管理页面](../rounds/P4-09.md) | 完成实际能力的可理解交互，区分用户和管理员。 | [P4-01](../rounds/P4-01.md)、[P4-07](../rounds/P4-07.md)、[P4-08](../rounds/P4-08.md) | 本组主责；核心开发范围 / 待开发 |

### P5 · 恢复、评测与受控试用

| 轮次与任务 | 目标 | 直接前置 | 范围/当前状态 |
| --- | --- | --- | --- |
| [P5-05 单用户工作区受控试用准备](../rounds/P5-05.md) | 把可用能力交给真实用户，保留账号和设备边界。 | [P5-03](../rounds/P5-03.md)、[P4-09](../rounds/P4-09.md) | 本组主责；核心开发范围 / 待开发 |

## 设计与接口入口

| 节点 | 详细设计 | 接口与对象入口 |
| --- | --- | --- |
| `ui` | [交互页面](../../design/components/ui.md) | [逐接口定义](../../api/nodes/ui.md) |
| `ingress` | [产品入口](../../design/components/ingress.md) | [逐接口定义](../../api/nodes/ingress.md) |
| `intent.preview` | [草稿理解预览](../../design/components/intent-preview.md) | [逐接口定义](../../api/nodes/intent.preview.md) |
| `run.approval` | [审批与用户控制](../../design/components/run-approval.md) | [逐接口定义](../../api/nodes/run.approval.md) |
| `workspace.binding` | [项目绑定与本地授权](../../design/components/workspace-binding.md) | [逐接口定义](../../api/nodes/workspace.binding.md) |
| `support.configuration` | [配置与账号控制层](../../design/components/support-configuration.md) | [逐接口定义](../../api/nodes/support.configuration.md) |

## 目标代码/验证目录

- `apps/web/src/features/workspace/`
- `src/uaw/api/ingress.py`
- `src/uaw/api/`
- `apps/web/src/features/chat/`
- `apps/web/src/features/review/`
- `apps/web/src/features/approvals/`
- `apps/web/src/features/agent_definitions/`
- `apps/web/src/features/run_controls/`
- `src/uaw/intent/preview.py`
- `src/uaw/run/approval.py`
- `apps/web/src/features/references/`
- `apps/web/src/features/admin/`
- `src/uaw/workspace/binding.py`
- `src/uaw/shared/configuration.py`
- `apps/web/`
- `apps/local_runner/`
- `ops/`

目录均为开发目标。每轮新增文件保持所属facade/port边界；共享设施分组不成为处理所有请求的统一业务Runtime。

## 本模块验收怎样汇总

按本页各轮验收与对应阶段真实场景确认。一个根节点关联到多轮，早期有最小实现不表示其记忆、并行、恢复等后续分支已完成；各能力要分别附代码/回执/版本。

