# Workspace与本地Runner · 开发计划

[计划总索引](../README.md) · [全局顺序与并行条件](../SEQUENCE.md)

## 职责与边界

本地授权、输入快照、隔离、环境、进程、成果和变更。

本分组主责6轮，另关联1轮跨模块协同。按阶段逐步完善，并与其他模块轮次交替接线；协同任务引用同一个工作包，不重复计算50轮总数。七Runtime是运行职责，11个计划分组包含工程、页面和后续适配，不是11个服务。

## 阶段与工作包

### P1 · 单Agent完整闭环

| 轮次与任务 | 目标 | 直接前置 | 范围/当前状态 |
| --- | --- | --- | --- |
| [P1-04 Runner配对与项目授权](../rounds/P1-04.md) | 让本机项目访问来自真实用户选择和设备授权。 | [P0-03](../rounds/P0-03.md)、[P1-03](../rounds/P1-03.md) | 本组主责；核心开发范围 / 待开发 |
| [P1-05 输入快照、隔离、环境和真实进程](../rounds/P1-05.md) | 运行真实项目检查并保留用户已有修改。 | [P1-04](../rounds/P1-04.md) | 本组主责；核心开发范围 / 待开发 |
| [P1-06 实际变更、成果与基础审阅](../rounds/P1-06.md) | 用户能看见这次工作改了什么并恢复文件。 | [P1-05](../rounds/P1-05.md) | 本组主责；核心开发范围 / 待开发 |

### P3 · 语义规划与并行协作

| 轮次与任务 | 目标 | 直接前置 | 范围/当前状态 |
| --- | --- | --- | --- |
| [P3-05 并行写隔离与三方合并](../rounds/P3-05.md) | 把子工作区修改安全纳入用户项目。 | [P3-04](../rounds/P3-04.md)、[P1-06](../rounds/P1-06.md) | 本组主责；核心开发范围 / 待开发 |
| [P3-06 块级审阅、局部应用与撤销](../rounds/P3-06.md) | 用户能选择具体改动和反馈位置。 | [P3-05](../rounds/P3-05.md) | 本组主责；核心开发范围 / 待开发 |

### P4 · 上下文、缓存与能力治理

| 轮次与任务 | 目标 | 直接前置 | 范围/当前状态 |
| --- | --- | --- | --- |
| [P4-07 多语言环境、进程回收与可选云后端](../rounds/P4-07.md) | 增加真实环境能力并保持安装和执行范围受控。 | [P4-06](../rounds/P4-06.md)、[P3-05](../rounds/P3-05.md) | 本组主责；核心开发范围 / 待开发 |

### P5 · 恢复、评测与受控试用

| 轮次与任务 | 目标 | 直接前置 | 范围/当前状态 |
| --- | --- | --- | --- |
| [P5-05 单用户工作区受控试用准备](../rounds/P5-05.md) | 把可用能力交给真实用户，保留账号和设备边界。 | [P5-03](../rounds/P5-03.md)、[P4-09](../rounds/P4-09.md) | 跨模块协同；核心开发范围 / 待开发 |

## 设计与接口入口

| 节点 | 详细设计 | 接口与对象入口 |
| --- | --- | --- |
| `workspace` | [工作区 · Workspace](../../design/modules/workspace.md) | [逐接口定义](../../api/nodes/workspace.md) |
| `workspace.binding` | [项目绑定与本地授权](../../design/components/workspace-binding.md) | [逐接口定义](../../api/nodes/workspace.binding.md) |
| `workspace.base` | [输入基础状态](../../design/components/workspace-base.md) | [逐接口定义](../../api/nodes/workspace.base.md) |
| `workspace.isolation` | [隔离与分支](../../design/components/workspace-isolation.md) | [逐接口定义](../../api/nodes/workspace.isolation.md) |
| `workspace.environment` | [环境准备与回收](../../design/components/workspace-environment.md) | [逐接口定义](../../api/nodes/workspace.environment.md) |
| `workspace.process` | [文件与进程执行](../../design/components/workspace-process.md) | [逐接口定义](../../api/nodes/workspace.process.md) |
| `workspace.changes` | [变更与冲突合并](../../design/components/workspace-changes.md) | [逐接口定义](../../api/nodes/workspace.changes.md) |
| `workspace.artifacts` | [产物与格式适配](../../design/components/workspace-artifacts.md) | [逐接口定义](../../api/nodes/workspace.artifacts.md) |
| `workspace.review` | [审阅与局部接受](../../design/components/workspace-review.md) | [逐接口定义](../../api/nodes/workspace.review.md) |
| `agent.definitions.change_service` | [配置变更与撤销](../../design/components/agent-definitions-change_service.md) | [逐接口定义](../../api/nodes/agent.definitions.change_service.md) |
| `agent.completion.version` | [版本与硬条件校验](../../design/components/agent-completion-version.md) | [逐接口定义](../../api/nodes/agent.completion.version.md) |
| `ingress` | [产品入口](../../design/components/ingress.md) | [逐接口定义](../../api/nodes/ingress.md) |
| `ui` | [交互页面](../../design/components/ui.md) | [逐接口定义](../../api/nodes/ui.md) |
| `support.configuration` | [配置与账号控制层](../../design/components/support-configuration.md) | [逐接口定义](../../api/nodes/support.configuration.md) |

## 目标代码/验证目录

- `src/uaw/workspace/facade.py`
- `src/uaw/workspace/binding.py`
- `apps/local_runner/uaw_runner/`
- `tests/integration/runner/`
- `src/uaw/workspace/base.py`
- `src/uaw/workspace/isolation.py`
- `src/uaw/workspace/environment.py`
- `src/uaw/workspace/process.py`
- `src/uaw/workspace/backends/`
- `tests/fixtures/projects/`
- `src/uaw/workspace/changes.py`
- `src/uaw/workspace/artifacts.py`
- `src/uaw/workspace/review.py`
- `tests/integration/delivery/`
- `tests/fixtures/git_projects/`
- `tests/integration/merge/`
- `src/uaw/agent/definitions/change_service.py`
- `src/uaw/agent/completion/version.py`
- `apps/web/src/features/review/`
- `tests/integration/partial_review/`
- `tests/fixtures/environments/`
- `src/uaw/api/ingress.py`
- `apps/web/src/features/workspace/`
- `src/uaw/shared/configuration.py`
- `src/uaw/api/`
- `apps/web/`
- `apps/local_runner/`
- `ops/`

目录均为开发目标。每轮新增文件保持所属facade/port边界；共享设施分组不成为处理所有请求的统一业务Runtime。

## 本模块验收怎样汇总

按本页各轮验收与对应阶段真实场景确认。一个根节点关联到多轮，早期有最小实现不表示其记忆、并行、恢复等后续分支已完成；各能力要分别附代码/回执/版本。

