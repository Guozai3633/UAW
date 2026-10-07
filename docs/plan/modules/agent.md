# Agent Runtime · 开发计划

[计划总索引](../README.md) · [全局顺序与并行条件](../SEQUENCE.md)

## 职责与边界

根循环、会话角色、子实例、技能、规划、调度和完成。

本分组主责11轮，另关联4轮跨模块协同。按阶段逐步完善，并与其他模块轮次交替接线；协同任务引用同一个工作包，不重复计算50轮总数。七Runtime是运行职责，11个计划分组包含工程、页面和后续适配，不是11个服务。

## 阶段与工作包

### P1 · 单Agent完整闭环

| 轮次与任务 | 目标 | 直接前置 | 范围/当前状态 |
| --- | --- | --- | --- |
| [P1-07 根实例、单Agent循环与工具接线](../rounds/P1-07.md) | 由主Agent动态决定下一步并完成实际工作。 | [P1-01](../rounds/P1-01.md)、[P1-02](../rounds/P1-02.md)、[P1-03](../rounds/P1-03.md)、[P1-05](../rounds/P1-05.md)、[P1-06](../rounds/P1-06.md) | 本组主责；核心开发范围 / 待开发 |
| [P1-08 交付契约、证据和完成提交](../rounds/P1-08.md) | 以真实要求、实际检查和版本决定是否完成。 | [P1-07](../rounds/P1-07.md) | 本组主责；核心开发范围 / 待开发 |

### P2 · 角色、子Agent与工作成果

| 轮次与任务 | 目标 | 直接前置 | 范围/当前状态 |
| --- | --- | --- | --- |
| [P2-03 技能加载与可复用任务模板](../rounds/P2-03.md) | 让操作方法按需复用而不靠长主提示词。 | [P2-01](../rounds/P2-01.md) | 本组主责；核心开发范围 / 待开发 |
| [P2-04 会话子Agent定义的设计和版本管理](../rounds/P2-04.md) | 用户可用自然语言创建、修改和撤销角色。 | [P2-03](../rounds/P2-03.md)、[P0-05](../rounds/P0-05.md) | 本组主责；核心开发范围 / 待开发 |
| [P2-05 首次有界子Agent调用](../rounds/P2-05.md) | 把定义转换为独立上下文和受限执行实例。 | [P2-04](../rounds/P2-04.md)、[P1-09](../rounds/P1-09.md) | 本组主责；核心开发范围 / 待开发 |
| [P2-06 共享结果板与Join](../rounds/P2-06.md) | 父Agent可靠收集结果并保留最终交付责任。 | [P2-05](../rounds/P2-05.md) | 本组主责；核心开发范围 / 待开发 |
| [P2-07 办公与学术方法和成果验收](../rounds/P2-07.md) | 在通用架构上实现两个可复用工作场景。 | [P2-02](../rounds/P2-02.md)、[P2-03](../rounds/P2-03.md)、[P2-06](../rounds/P2-06.md) | 本组主责；核心开发范围 / 待开发 |

### P3 · 语义规划与并行协作

| 轮次与任务 | 目标 | 直接前置 | 范围/当前状态 |
| --- | --- | --- | --- |
| [P3-01 语义执行评估与步骤计划](../rounds/P3-01.md) | 独立判断规划、委派、并发和信息缺口。 | [P2-09](../rounds/P2-09.md) | 本组主责；核心开发范围 / 待开发 |
| [P3-02 DAG验证与有界调度](../rounds/P3-02.md) | 以真实依赖和资源执行任务图。 | [P3-01](../rounds/P3-01.md) | 本组主责；核心开发范围 / 待开发 |
| [P3-04 多个子Agent并行与树级约束](../rounds/P3-04.md) | 运行多个独立分工并控制父子深度、预算和取消。 | [P3-02](../rounds/P3-02.md)、[P2-06](../rounds/P2-06.md) | 本组主责；核心开发范围 / 待开发 |
| [P3-06 块级审阅、局部应用与撤销](../rounds/P3-06.md) | 用户能选择具体改动和反馈位置。 | [P3-05](../rounds/P3-05.md) | 跨模块协同；核心开发范围 / 待开发 |
| [P3-07 复杂运行干预与多会话任务](../rounds/P3-07.md) | 处理目标修订、排队、部分交付和同用户共享任务。 | [P3-04](../rounds/P3-04.md)、[P3-06](../rounds/P3-06.md) | 跨模块协同；核心开发范围 / 待开发 |

### P4 · 上下文、缓存与能力治理

| 轮次与任务 | 目标 | 直接前置 | 范围/当前状态 |
| --- | --- | --- | --- |
| [P4-03 角色过滤与向量混合发现](../rounds/P4-03.md) | 扩大工具目录而保留LLM最终选择。 | [P4-02](../rounds/P4-02.md)、[P2-04](../rounds/P2-04.md) | 跨模块协同；核心开发范围 / 待开发 |
| [P4-08 明确Auto授权与能力恢复](../rounds/P4-08.md) | 固定模型仍不变，Auto只能在用户授权范围内选择。 | [P4-06](../rounds/P4-06.md)、[P3-08](../rounds/P3-08.md) | 跨模块协同；核心开发范围 / 待开发 |

### P5 · 恢复、评测与受控试用

| 轮次与任务 | 目标 | 直接前置 | 范围/当前状态 |
| --- | --- | --- | --- |
| [P5-04 handoff与定时扩展实现](../rounds/P5-04.md) | 完善已规划扩展，但独立UAW首个试用默认关闭。 | [P5-02](../rounds/P5-02.md)、[P3-04](../rounds/P3-04.md) | 本组主责；目标：实现后默认关闭；不挡首次试用 / 待开发 |

## 设计与接口入口

| 节点 | 详细设计 | 接口与对象入口 |
| --- | --- | --- |
| `agent` | [决策执行 · Agent](../../design/modules/agent.md) | [逐接口定义](../../api/nodes/agent.md) |
| `agent.factory` | [统一实例工厂](../../design/components/agent-factory.md) | [逐接口定义](../../api/nodes/agent.factory.md) |
| `agent.loop` | [Agent 决策循环](../../design/components/agent-loop.md) | [逐接口定义](../../api/nodes/agent.loop.md) |
| `agent.completion` | [完成核验协调](../../design/components/agent-completion.md) | [逐接口定义](../../api/nodes/agent.completion.md) |
| `agent.completion.contract` | [语义交付契约](../../design/components/agent-completion-contract.md) | [逐接口定义](../../api/nodes/agent.completion.contract.md) |
| `agent.completion.evidence` | [真实证据收集](../../design/components/agent-completion-evidence.md) | [逐接口定义](../../api/nodes/agent.completion.evidence.md) |
| `agent.completion.semantic` | [语义核对](../../design/components/agent-completion-semantic.md) | [逐接口定义](../../api/nodes/agent.completion.semantic.md) |
| `agent.completion.version` | [版本与硬条件校验](../../design/components/agent-completion-version.md) | [逐接口定义](../../api/nodes/agent.completion.version.md) |
| `agent.completion.delivery` | [提交交付](../../design/components/agent-completion-delivery.md) | [逐接口定义](../../api/nodes/agent.completion.delivery.md) |
| `agent.completion.acceptance` | [用户接受与迭代](../../design/components/agent-completion-acceptance.md) | [逐接口定义](../../api/nodes/agent.completion.acceptance.md) |
| `agent.skills` | [技能与任务模板](../../design/components/agent-skills.md) | [逐接口定义](../../api/nodes/agent.skills.md) |
| `context.rules` | [规则与信任装配](../../design/components/context-rules.md) | [逐接口定义](../../api/nodes/context.rules.md) |
| `agent.definitions` | [子Agent定义与发现](../../design/components/agent-definitions.md) | [逐接口定义](../../api/nodes/agent.definitions.md) |
| `agent.definitions.designer` | [角色设计方法](../../design/components/agent-definitions-designer.md) | [逐接口定义](../../api/nodes/agent.definitions.designer.md) |
| `agent.definitions.validator` | [定义与授权校验](../../design/components/agent-definitions-validator.md) | [逐接口定义](../../api/nodes/agent.definitions.validator.md) |
| `agent.definitions.model_intent` | [模型意图解析](../../design/components/agent-definitions-model_intent.md) | [逐接口定义](../../api/nodes/agent.definitions.model_intent.md) |
| `agent.definitions.repository` | [定义提交与版本](../../design/components/agent-definitions-repository.md) | [逐接口定义](../../api/nodes/agent.definitions.repository.md) |
| `agent.definitions.discovery` | [会话Agent发现](../../design/components/agent-definitions-discovery.md) | [逐接口定义](../../api/nodes/agent.definitions.discovery.md) |
| `agent.definitions.change_service` | [配置变更与撤销](../../design/components/agent-definitions-change_service.md) | [逐接口定义](../../api/nodes/agent.definitions.change_service.md) |
| `agent.collaboration` | [委派与控制权](../../design/components/agent-collaboration.md) | [逐接口定义](../../api/nodes/agent.collaboration.md) |
| `agent.collaboration.contract` | [子任务契约](../../design/components/agent-collaboration-contract.md) | [逐接口定义](../../api/nodes/agent.collaboration.contract.md) |
| `agent.collaboration.instance` | [隔离运行实例](../../design/components/agent-collaboration-instance.md) | [逐接口定义](../../api/nodes/agent.collaboration.instance.md) |
| `agent.collaboration.channel` | [消息与受控引用](../../design/components/agent-collaboration-channel.md) | [逐接口定义](../../api/nodes/agent.collaboration.channel.md) |
| `agent.collaboration.cancel` | [生命周期与取消](../../design/components/agent-collaboration-cancel.md) | [逐接口定义](../../api/nodes/agent.collaboration.cancel.md) |
| `agent.board` | [共享任务板](../../design/components/agent-board.md) | [逐接口定义](../../api/nodes/agent.board.md) |
| `agent.collaboration.join` | [结果核验与汇总](../../design/components/agent-collaboration-join.md) | [逐接口定义](../../api/nodes/agent.collaboration.join.md) |
| `context.references` | [引用登记与解析](../../design/components/context-references.md) | [逐接口定义](../../api/nodes/context.references.md) |
| `agent.assessment` | [按需执行评估](../../design/components/agent-assessment.md) | [逐接口定义](../../api/nodes/agent.assessment.md) |
| `agent.planning` | [规划与依赖校验](../../design/components/agent-planning.md) | [逐接口定义](../../api/nodes/agent.planning.md) |
| `intent.references` | [指代解析](../../design/components/intent-references.md) | [逐接口定义](../../api/nodes/intent.references.md) |
| `intent.probe` | [必要信息探查](../../design/components/intent-probe.md) | [逐接口定义](../../api/nodes/intent.probe.md) |
| `intent.ambiguity` | [歧义处理](../../design/components/intent-ambiguity.md) | [逐接口定义](../../api/nodes/intent.ambiguity.md) |
| `agent.scheduler` | [节点与资源调度](../../design/components/agent-scheduler.md) | [逐接口定义](../../api/nodes/agent.scheduler.md) |
| `workspace.review` | [审阅与局部接受](../../design/components/workspace-review.md) | [逐接口定义](../../api/nodes/workspace.review.md) |
| `workspace.changes` | [变更与冲突合并](../../design/components/workspace-changes.md) | [逐接口定义](../../api/nodes/workspace.changes.md) |
| `workspace.artifacts` | [产物与格式适配](../../design/components/workspace-artifacts.md) | [逐接口定义](../../api/nodes/workspace.artifacts.md) |
| `run.approval` | [审批与用户控制](../../design/components/run-approval.md) | [逐接口定义](../../api/nodes/run.approval.md) |
| `run.cancel` | [取消传播](../../design/components/run-cancel.md) | [逐接口定义](../../api/nodes/run.cancel.md) |
| `run.history` | [历史与输入权威](../../design/components/run-history.md) | [逐接口定义](../../api/nodes/run.history.md) |
| `run.state` | [Run 与交互项](../../design/components/run-state.md) | [逐接口定义](../../api/nodes/run.state.md) |
| `tool.registry` | [工具注册与版本](../../design/components/tool-registry.md) | [逐接口定义](../../api/nodes/tool.registry.md) |
| `tool.discovery` | [工具发现与筛选](../../design/components/tool-discovery.md) | [逐接口定义](../../api/nodes/tool.discovery.md) |
| `context.retrieval` | [资料检索与证据](../../design/components/context-retrieval.md) | [逐接口定义](../../api/nodes/context.retrieval.md) |
| `model.policy` | [选择与模型继承](../../design/components/model-policy.md) | [逐接口定义](../../api/nodes/model.policy.md) |
| `model.capability` | [兼容与Auto选择](../../design/components/model-capability.md) | [逐接口定义](../../api/nodes/model.capability.md) |
| `model.catalog` | [可见模型目录](../../design/components/model-catalog.md) | [逐接口定义](../../api/nodes/model.catalog.md) |
| `model.recovery` | [调用恢复](../../design/components/model-recovery.md) | [逐接口定义](../../api/nodes/model.recovery.md) |
| `model.usage` | [计量与版本记录](../../design/components/model-usage.md) | [逐接口定义](../../api/nodes/model.usage.md) |
| `agent.collaboration.handoff` | [可选控制权交接](../../design/components/agent-collaboration-handoff.md) | [逐接口定义](../../api/nodes/agent.collaboration.handoff.md) |
| `run.trigger` | [未来触发器](../../design/components/run-trigger.md) | [逐接口定义](../../api/nodes/run.trigger.md) |

## 目标代码/验证目录

- `src/uaw/agent/facade.py`
- `src/uaw/agent/factory.py`
- `src/uaw/agent/loop.py`
- `src/uaw/tool/control/`
- `src/uaw/agent/engines/`
- `tests/integration/agent/`
- `src/uaw/agent/completion/facade.py`
- `src/uaw/agent/completion/contract.py`
- `src/uaw/agent/completion/evidence.py`
- `src/uaw/agent/completion/semantic.py`
- `src/uaw/agent/completion/version.py`
- `src/uaw/agent/completion/delivery.py`
- `src/uaw/agent/completion/acceptance.py`
- `tests/integration/completion/`
- `src/uaw/agent/skills.py`
- `src/uaw/context/rules.py`
- `capabilities/builtin/`
- `tests/integration/skills/`
- `src/uaw/agent/definitions/facade.py`
- `src/uaw/agent/definitions/designer.py`
- `src/uaw/agent/definitions/validator.py`
- `src/uaw/agent/definitions/model_intent.py`
- `src/uaw/agent/definitions/repository.py`
- `src/uaw/agent/definitions/discovery.py`
- `src/uaw/agent/definitions/change_service.py`
- `src/uaw/agent/definitions/`
- `prompts/`
- `src/uaw/agent/collaboration/facade.py`
- `src/uaw/agent/collaboration/contract.py`
- `src/uaw/agent/collaboration/instance.py`
- `src/uaw/agent/collaboration/channel.py`
- `src/uaw/agent/collaboration/cancel.py`
- `src/uaw/agent/collaboration/`
- `tests/integration/subagents/`
- `src/uaw/agent/board.py`
- `src/uaw/agent/collaboration/join.py`
- `tests/integration/join/`
- `src/uaw/context/references.py`
- `capabilities/builtin/office_report/`
- `capabilities/builtin/academic_discussion/`
- `tests/fixtures/scenarios/`
- `src/uaw/agent/assessment.py`
- `src/uaw/agent/planning.py`
- `src/uaw/intent/references.py`
- `src/uaw/intent/probe.py`
- `src/uaw/intent/ambiguity.py`
- `tests/fixtures/assessments/`
- `src/uaw/agent/scheduler.py`
- `tests/integration/scheduler/`
- `tests/integration/agent_parallel/`
- `src/uaw/workspace/review.py`
- `src/uaw/workspace/changes.py`
- `src/uaw/workspace/artifacts.py`
- `apps/web/src/features/review/`
- `tests/integration/partial_review/`
- `src/uaw/run/approval.py`
- `src/uaw/run/cancel.py`
- `src/uaw/run/history.py`
- `src/uaw/run/state.py`
- `apps/web/src/features/run_controls/`
- `tests/integration/multi_conversation/`
- `src/uaw/tool/registry.py`
- `src/uaw/tool/discovery.py`
- `src/uaw/context/retrieval.py`
- `tests/evaluation/tool_discovery/`
- `src/uaw/model/policy.py`
- `src/uaw/model/capability.py`
- `src/uaw/model/catalog.py`
- `src/uaw/model/recovery.py`
- `src/uaw/model/usage.py`
- `tests/integration/model_policy/`
- `tests/evaluation/model_selection/`
- `src/uaw/agent/collaboration/handoff.py`
- `src/uaw/run/trigger.py`
- `tests/integration/handoff/`
- `tests/integration/triggers/`

目录均为开发目标。每轮新增文件保持所属facade/port边界；共享设施分组不成为处理所有请求的统一业务Runtime。

## 本模块验收怎样汇总

按本页各轮验收与对应阶段真实场景确认。一个根节点关联到多轮，早期有最小实现不表示其记忆、并行、恢复等后续分支已完成；各能力要分别附代码/回执/版本。

