# Intent Runtime · 开发计划

[计划总索引](../README.md) · [全局顺序与并行条件](../SEQUENCE.md)

## 职责与边界

用户原文加工、正式理解、未知项与只读草稿提示。

本分组主责1轮，另关联2轮跨模块协同。按阶段逐步完善，并与其他模块轮次交替接线；协同任务引用同一个工作包，不重复计算50轮总数。七Runtime是运行职责，11个计划分组包含工程、页面和后续适配，不是11个服务。

## 阶段与工作包

### P1 · 单Agent完整闭环

| 轮次与任务 | 目标 | 直接前置 | 范围/当前状态 |
| --- | --- | --- | --- |
| [P1-01 正式任务理解与原文溯源](../rounds/P1-01.md) | 得到有版本、可纠正的TaskFrame。 | [P0-04](../rounds/P0-04.md)、[P0-05](../rounds/P0-05.md) | 本组主责；核心开发范围 / 开发中 |

### P3 · 语义规划与并行协作

| 轮次与任务 | 目标 | 直接前置 | 范围/当前状态 |
| --- | --- | --- | --- |
| [P3-01 语义执行评估与步骤计划](../rounds/P3-01.md) | 独立判断规划、委派、并发和信息缺口。 | [P2-09](../rounds/P2-09.md) | 跨模块协同；核心开发范围 / 待开发 |

### P4 · 上下文、缓存与能力治理

| 轮次与任务 | 目标 | 直接前置 | 范围/当前状态 |
| --- | --- | --- | --- |
| [P4-09 草稿提示、用户控制与完整管理页面](../rounds/P4-09.md) | 完成实际能力的可理解交互，区分用户和管理员。 | [P4-01](../rounds/P4-01.md)、[P4-07](../rounds/P4-07.md)、[P4-08](../rounds/P4-08.md) | 跨模块协同；核心开发范围 / 待开发 |

## 设计与接口入口

| 节点 | 详细设计 | 接口与对象入口 |
| --- | --- | --- |
| `intent` | [任务理解 · Intent](../../design/modules/intent.md) | [逐接口定义](../../api/nodes/intent.md) |
| `intent.original` | [原文读取](../../design/components/intent-original.md) | [逐接口定义](../../api/nodes/intent.original.md) |
| `intent.semantic` | [语义解析](../../design/components/intent-semantic.md) | [逐接口定义](../../api/nodes/intent.semantic.md) |
| `intent.frame` | [任务框架](../../design/components/intent-frame.md) | [逐接口定义](../../api/nodes/intent.frame.md) |
| `agent.assessment` | [按需执行评估](../../design/components/agent-assessment.md) | [逐接口定义](../../api/nodes/agent.assessment.md) |
| `agent.planning` | [规划与依赖校验](../../design/components/agent-planning.md) | [逐接口定义](../../api/nodes/agent.planning.md) |
| `intent.references` | [指代解析](../../design/components/intent-references.md) | [逐接口定义](../../api/nodes/intent.references.md) |
| `intent.probe` | [必要信息探查](../../design/components/intent-probe.md) | [逐接口定义](../../api/nodes/intent.probe.md) |
| `intent.ambiguity` | [歧义处理](../../design/components/intent-ambiguity.md) | [逐接口定义](../../api/nodes/intent.ambiguity.md) |
| `ui` | [交互页面](../../design/components/ui.md) | [逐接口定义](../../api/nodes/ui.md) |
| `ingress` | [产品入口](../../design/components/ingress.md) | [逐接口定义](../../api/nodes/ingress.md) |
| `intent.preview` | [草稿理解预览](../../design/components/intent-preview.md) | [逐接口定义](../../api/nodes/intent.preview.md) |
| `run.approval` | [审批与用户控制](../../design/components/run-approval.md) | [逐接口定义](../../api/nodes/run.approval.md) |

## 目标代码/验证目录

- `src/uaw/intent/facade.py`
- `src/uaw/intent/original.py`
- `src/uaw/intent/semantic.py`
- `src/uaw/intent/frame.py`
- `prompts/`
- `tests/integration/intent/`
- `src/uaw/agent/assessment.py`
- `src/uaw/agent/planning.py`
- `src/uaw/intent/references.py`
- `src/uaw/intent/probe.py`
- `src/uaw/intent/ambiguity.py`
- `tests/fixtures/assessments/`
- `apps/web/src/features/workspace/`
- `src/uaw/api/ingress.py`
- `src/uaw/intent/preview.py`
- `src/uaw/run/approval.py`
- `apps/web/src/features/approvals/`
- `apps/web/src/features/references/`
- `apps/web/src/features/admin/`

目录均为开发目标。每轮新增文件保持所属facade/port边界；共享设施分组不成为处理所有请求的统一业务Runtime。

## 本模块验收怎样汇总

按本页各轮验收与对应阶段真实场景确认。一个根节点关联到多轮，早期有最小实现不表示其记忆、并行、恢复等后续分支已完成；各能力要分别附代码/回执/版本。

