# Run Runtime · 开发计划

[计划总索引](../README.md) · [全局顺序与并行条件](../SEQUENCE.md)

## 职责与边界

原文与历史、执行状态、审批、预算、取消、检查点和恢复。

本分组主责5轮，另关联3轮跨模块协同。按阶段逐步完善，并与其他模块轮次交替接线；协同任务引用同一个工作包，不重复计算50轮总数。七Runtime是运行职责，11个计划分组包含工程、页面和后续适配，不是11个服务。

## 阶段与工作包

### P0 · 工程起步与基础边界

| 轮次与任务 | 目标 | 直接前置 | 范围/当前状态 |
| --- | --- | --- | --- |
| [P0-04 受理、原文、状态、事件与资源账本](../rounds/P0-04.md) | 保存原文并以真实状态和用量驱动后续执行。 | [P0-02](../rounds/P0-02.md)、[P0-03](../rounds/P0-03.md) | 本组主责；核心开发范围 / 已验收 |

### P1 · 单Agent完整闭环

| 轮次与任务 | 目标 | 直接前置 | 范围/当前状态 |
| --- | --- | --- | --- |
| [P1-09 人工审批、基础干预与取消](../rounds/P1-09.md) | 用户可停止或修正当前单Agent任务。 | [P1-07](../rounds/P1-07.md)、[P1-08](../rounds/P1-08.md) | 本组主责；核心开发范围 / 待开发 |

### P3 · 语义规划与并行协作

| 轮次与任务 | 目标 | 直接前置 | 范围/当前状态 |
| --- | --- | --- | --- |
| [P3-03 独立工具并发与回压](../rounds/P3-03.md) | 只并发可证明独立的动作，并保持账本正确。 | [P3-02](../rounds/P3-02.md) | 跨模块协同；核心开发范围 / 待开发 |
| [P3-07 复杂运行干预与多会话任务](../rounds/P3-07.md) | 处理目标修订、排队、部分交付和同用户共享任务。 | [P3-04](../rounds/P3-04.md)、[P3-06](../rounds/P3-06.md) | 本组主责；核心开发范围 / 待开发 |

### P4 · 上下文、缓存与能力治理

| 轮次与任务 | 目标 | 直接前置 | 范围/当前状态 |
| --- | --- | --- | --- |
| [P4-09 草稿提示、用户控制与完整管理页面](../rounds/P4-09.md) | 完成实际能力的可理解交互，区分用户和管理员。 | [P4-01](../rounds/P4-01.md)、[P4-07](../rounds/P4-07.md)、[P4-08](../rounds/P4-08.md) | 跨模块协同；核心开发范围 / 待开发 |

### P5 · 恢复、评测与受控试用

| 轮次与任务 | 目标 | 直接前置 | 范围/当前状态 |
| --- | --- | --- | --- |
| [P5-01 跨域检查点与一致提交边界](../rounds/P5-01.md) | 保存可核验的续跑位置和未决动作。 | [P4-10](../rounds/P4-10.md) | 本组主责；核心开发范围 / 待开发 |
| [P5-02 租约、当前权限与安全续跑](../rounds/P5-02.md) | 恢复未完工作而不重复未知外部写。 | [P5-01](../rounds/P5-01.md) | 本组主责；核心开发范围 / 待开发 |
| [P5-04 handoff与定时扩展实现](../rounds/P5-04.md) | 完善已规划扩展，但独立UAW首个试用默认关闭。 | [P5-02](../rounds/P5-02.md)、[P3-04](../rounds/P3-04.md) | 跨模块协同；目标：实现后默认关闭；不挡首次试用 / 待开发 |

## 设计与接口入口

| 节点 | 详细设计 | 接口与对象入口 |
| --- | --- | --- |
| `run` | [运行控制 · Run](../../design/modules/run.md) | [逐接口定义](../../api/nodes/run.md) |
| `run.history` | [历史与输入权威](../../design/components/run-history.md) | [逐接口定义](../../api/nodes/run.history.md) |
| `run.state` | [Run 与交互项](../../design/components/run-state.md) | [逐接口定义](../../api/nodes/run.state.md) |
| `run.events` | [事件与重连](../../design/components/run-events.md) | [逐接口定义](../../api/nodes/run.events.md) |
| `run.budget` | [预算与准入](../../design/components/run-budget.md) | [逐接口定义](../../api/nodes/run.budget.md) |
| `support.observability` | [运行观测](../../design/components/support-observability.md) | [逐接口定义](../../api/nodes/support.observability.md) |
| `run.approval` | [审批与用户控制](../../design/components/run-approval.md) | [逐接口定义](../../api/nodes/run.approval.md) |
| `run.cancel` | [取消传播](../../design/components/run-cancel.md) | [逐接口定义](../../api/nodes/run.cancel.md) |
| `tool.invocation` | [调用闸门与派发](../../design/components/tool-invocation.md) | [逐接口定义](../../api/nodes/tool.invocation.md) |
| `tool.effects` | [调用与副作用账本](../../design/components/tool-effects.md) | [逐接口定义](../../api/nodes/tool.effects.md) |
| `agent.planning` | [规划与依赖校验](../../design/components/agent-planning.md) | [逐接口定义](../../api/nodes/agent.planning.md) |
| `agent.board` | [共享任务板](../../design/components/agent-board.md) | [逐接口定义](../../api/nodes/agent.board.md) |
| `ui` | [交互页面](../../design/components/ui.md) | [逐接口定义](../../api/nodes/ui.md) |
| `ingress` | [产品入口](../../design/components/ingress.md) | [逐接口定义](../../api/nodes/ingress.md) |
| `intent.preview` | [草稿理解预览](../../design/components/intent-preview.md) | [逐接口定义](../../api/nodes/intent.preview.md) |
| `run.checkpoint` | [恢复边界与版本](../../design/components/run-checkpoint.md) | [逐接口定义](../../api/nodes/run.checkpoint.md) |
| `run.resume` | [租约与执行恢复](../../design/components/run-resume.md) | [逐接口定义](../../api/nodes/run.resume.md) |
| `run.resume.lease` | [取得运行租约](../../design/components/run-resume-lease.md) | [逐接口定义](../../api/nodes/run.resume.lease.md) |
| `run.resume.versions` | [版本兼容检查](../../design/components/run-resume-versions.md) | [逐接口定义](../../api/nodes/run.resume.versions.md) |
| `run.resume.access` | [重建连接与核验](../../design/components/run-resume-access.md) | [逐接口定义](../../api/nodes/run.resume.access.md) |
| `run.resume.effects` | [Tool未决动作对账](../../design/components/run-resume-effects.md) | [逐接口定义](../../api/nodes/run.resume.effects.md) |
| `run.resume.workspace` | [工作区实际版本](../../design/components/run-resume-workspace.md) | [逐接口定义](../../api/nodes/run.resume.workspace.md) |
| `run.resume.continue` | [恢复可运行工作](../../design/components/run-resume-continue.md) | [逐接口定义](../../api/nodes/run.resume.continue.md) |
| `agent.collaboration.handoff` | [可选控制权交接](../../design/components/agent-collaboration-handoff.md) | [逐接口定义](../../api/nodes/agent.collaboration.handoff.md) |
| `run.trigger` | [未来触发器](../../design/components/run-trigger.md) | [逐接口定义](../../api/nodes/run.trigger.md) |

## 目标代码/验证目录

- `src/uaw/run/facade.py`
- `src/uaw/run/history.py`
- `src/uaw/run/state.py`
- `src/uaw/run/events.py`
- `src/uaw/run/budget.py`
- `src/uaw/shared/observability.py`
- `tests/integration/run/`
- `src/uaw/run/approval.py`
- `src/uaw/run/cancel.py`
- `tests/integration/control/`
- `src/uaw/tool/invocation/facade.py`
- `src/uaw/tool/effects.py`
- `tests/integration/tool_parallel/`
- `src/uaw/agent/planning.py`
- `src/uaw/agent/board.py`
- `apps/web/src/features/run_controls/`
- `tests/integration/multi_conversation/`
- `apps/web/src/features/workspace/`
- `src/uaw/api/ingress.py`
- `src/uaw/intent/preview.py`
- `apps/web/src/features/approvals/`
- `apps/web/src/features/references/`
- `apps/web/src/features/admin/`
- `src/uaw/run/checkpoint.py`
- `tests/integration/checkpoint/`
- `src/uaw/run/resume/facade.py`
- `src/uaw/run/resume/lease.py`
- `src/uaw/run/resume/versions.py`
- `src/uaw/run/resume/access.py`
- `src/uaw/run/resume/effects.py`
- `src/uaw/run/resume/workspace.py`
- `src/uaw/run/resume/continue_run.py`
- `tests/integration/recovery/`
- `apps/local_runner/uaw_runner/`
- `src/uaw/agent/collaboration/handoff.py`
- `src/uaw/run/trigger.py`
- `tests/integration/handoff/`
- `tests/integration/triggers/`

目录均为开发目标。每轮新增文件保持所属facade/port边界；共享设施分组不成为处理所有请求的统一业务Runtime。

## 本模块验收怎样汇总

按本页各轮验收与对应阶段真实场景确认。一个根节点关联到多轮，早期有最小实现不表示其记忆、并行、恢复等后续分支已完成；各能力要分别附代码/回执/版本。

