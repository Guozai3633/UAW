# UAW 开发设计总索引

状态：v0.10 · 2026-10-07。每个图节点有单独文档与计划代码位置；所有代码目标均待实现，文档覆盖不代表实现或已完成任务验证。

[全局指引](../../README.md) · [项目目录](../PROJECT_STRUCTURE.md) · [文档作用地图](../DOCUMENT_MAP.md) · [公共契约](COMMON_CONTRACTS.md) · [子Agent完整链路](SUBAGENT_LIFECYCLE.md)

## 从哪里开始

1. 先看 SUBAGENT_LIFECYCLE 和 PROJECT_STRUCTURE，确认端到端行为与开发组织。
2. 再看 modules/ 下对应大模块，进入其 components/ 子节点文档。
3. 图谱节点中的‘开发设计’链接与下表完全对应。修改策略先改 design/catalog.py，再重建文档和图谱。

## 交互页面

| 节点 | 开发策略文档 | 计划代码位置 |
| --- | --- | --- |
| `ui` | [交互页面](components/ui.md) | `apps/web/src/features/workspace/` |

## 产品入口

| 节点 | 开发策略文档 | 计划代码位置 |
| --- | --- | --- |
| `ingress` | [产品入口](components/ingress.md) | `src/uaw/api/ingress.py` |

## 任务理解 · Intent

| 节点 | 开发策略文档 | 计划代码位置 |
| --- | --- | --- |
| `intent` | [任务理解 · Intent](modules/intent.md) | `src/uaw/intent/facade.py` |
| `intent.preview` | [草稿理解预览](components/intent-preview.md) | `src/uaw/intent/preview.py` |
| `intent.original` | [原文读取](components/intent-original.md) | `src/uaw/intent/original.py` |
| `intent.semantic` | [语义解析](components/intent-semantic.md) | `src/uaw/intent/semantic.py` |
| `intent.references` | [指代解析](components/intent-references.md) | `src/uaw/intent/references.py` |
| `intent.probe` | [必要信息探查](components/intent-probe.md) | `src/uaw/intent/probe.py` |
| `intent.ambiguity` | [歧义处理](components/intent-ambiguity.md) | `src/uaw/intent/ambiguity.py` |
| `intent.frame` | [任务框架](components/intent-frame.md) | `src/uaw/intent/frame.py` |

## 决策执行 · Agent

| 节点 | 开发策略文档 | 计划代码位置 |
| --- | --- | --- |
| `agent` | [决策执行 · Agent](modules/agent.md) | `src/uaw/agent/facade.py` |
| `agent.definitions` | [子Agent定义与发现](components/agent-definitions.md) | `src/uaw/agent/definitions/facade.py` |
| `agent.loop` | [Agent 决策循环](components/agent-loop.md) | `src/uaw/agent/loop.py` |
| `agent.assessment` | [按需执行评估](components/agent-assessment.md) | `src/uaw/agent/assessment.py` |
| `agent.planning` | [规划与依赖校验](components/agent-planning.md) | `src/uaw/agent/planning.py` |
| `agent.scheduler` | [节点与资源调度](components/agent-scheduler.md) | `src/uaw/agent/scheduler.py` |
| `agent.collaboration` | [委派与控制权](components/agent-collaboration.md) | `src/uaw/agent/collaboration/facade.py` |
| `agent.skills` | [技能与任务模板](components/agent-skills.md) | `src/uaw/agent/skills.py` |
| `agent.completion` | [完成核验协调](components/agent-completion.md) | `src/uaw/agent/completion/facade.py` |
| `agent.board` | [共享任务板](components/agent-board.md) | `src/uaw/agent/board.py` |
| `agent.factory` | [统一实例工厂](components/agent-factory.md) | `src/uaw/agent/factory.py` |
| `agent.definitions.designer` | [角色设计方法](components/agent-definitions-designer.md) | `src/uaw/agent/definitions/designer.py` |
| `agent.definitions.validator` | [定义与授权校验](components/agent-definitions-validator.md) | `src/uaw/agent/definitions/validator.py` |
| `agent.definitions.model_intent` | [模型意图解析](components/agent-definitions-model_intent.md) | `src/uaw/agent/definitions/model_intent.py` |
| `agent.definitions.repository` | [定义提交与版本](components/agent-definitions-repository.md) | `src/uaw/agent/definitions/repository.py` |
| `agent.definitions.discovery` | [会话Agent发现](components/agent-definitions-discovery.md) | `src/uaw/agent/definitions/discovery.py` |
| `agent.definitions.change_service` | [配置变更与撤销](components/agent-definitions-change_service.md) | `src/uaw/agent/definitions/change_service.py` |
| `agent.collaboration.contract` | [子任务契约](components/agent-collaboration-contract.md) | `src/uaw/agent/collaboration/contract.py` |
| `agent.collaboration.instance` | [隔离运行实例](components/agent-collaboration-instance.md) | `src/uaw/agent/collaboration/instance.py` |
| `agent.collaboration.channel` | [消息与受控引用](components/agent-collaboration-channel.md) | `src/uaw/agent/collaboration/channel.py` |
| `agent.collaboration.join` | [结果核验与汇总](components/agent-collaboration-join.md) | `src/uaw/agent/collaboration/join.py` |
| `agent.collaboration.handoff` | [可选控制权交接](components/agent-collaboration-handoff.md) | `src/uaw/agent/collaboration/handoff.py` |
| `agent.collaboration.cancel` | [生命周期与取消](components/agent-collaboration-cancel.md) | `src/uaw/agent/collaboration/cancel.py` |
| `agent.completion.contract` | [语义交付契约](components/agent-completion-contract.md) | `src/uaw/agent/completion/contract.py` |
| `agent.completion.evidence` | [真实证据收集](components/agent-completion-evidence.md) | `src/uaw/agent/completion/evidence.py` |
| `agent.completion.semantic` | [语义核对](components/agent-completion-semantic.md) | `src/uaw/agent/completion/semantic.py` |
| `agent.completion.version` | [版本与硬条件校验](components/agent-completion-version.md) | `src/uaw/agent/completion/version.py` |
| `agent.completion.delivery` | [提交交付](components/agent-completion-delivery.md) | `src/uaw/agent/completion/delivery.py` |
| `agent.completion.acceptance` | [用户接受与迭代](components/agent-completion-acceptance.md) | `src/uaw/agent/completion/acceptance.py` |

## 上下文 · Context

| 节点 | 开发策略文档 | 计划代码位置 |
| --- | --- | --- |
| `context` | [上下文 · Context](modules/context.md) | `src/uaw/context/facade.py` |
| `context.sources` | [来源解析](components/context-sources.md) | `src/uaw/context/sources.py` |
| `context.rules` | [规则与信任装配](components/context-rules.md) | `src/uaw/context/rules.py` |
| `context.ingestion` | [摄取与索引发布](components/context-ingestion.md) | `src/uaw/context/ingestion.py` |
| `context.retrieval` | [资料检索与证据](components/context-retrieval.md) | `src/uaw/context/retrieval.py` |
| `context.memory` | [记忆生命周期](components/context-memory.md) | `src/uaw/context/memory/facade.py` |
| `context.selection` | [选择与上下文预算](components/context-selection.md) | `src/uaw/context/selection.py` |
| `context.compression` | [压缩与关键项保护](components/context-compression.md) | `src/uaw/context/compression.py` |
| `context.composer` | [装配与快照](components/context-composer.md) | `src/uaw/context/composer.py` |
| `context.references` | [引用登记与解析](components/context-references.md) | `src/uaw/context/references.py` |
| `context.memory.candidate` | [记忆候选](components/context-memory-candidate.md) | `src/uaw/context/memory/candidate.py` |
| `context.memory.policy` | [范围与写入政策](components/context-memory-policy.md) | `src/uaw/context/memory/policy.py` |
| `context.memory.conflict` | [查重与冲突](components/context-memory-conflict.md) | `src/uaw/context/memory/conflict.py` |
| `context.memory.store` | [提交与召回](components/context-memory-store.md) | `src/uaw/context/memory/store.py` |
| `context.memory.forget` | [遗忘与删除传播](components/context-memory-forget.md) | `src/uaw/context/memory/forget.py` |

## 工具执行 · Tool

| 节点 | 开发策略文档 | 计划代码位置 |
| --- | --- | --- |
| `tool` | [工具执行 · Tool](modules/tool.md) | `src/uaw/tool/facade.py` |
| `tool.registry` | [工具注册与版本](components/tool-registry.md) | `src/uaw/tool/registry.py` |
| `tool.discovery` | [工具发现与筛选](components/tool-discovery.md) | `src/uaw/tool/discovery.py` |
| `tool.invocation` | [调用闸门与派发](components/tool-invocation.md) | `src/uaw/tool/invocation/facade.py` |
| `tool.effects` | [调用与副作用账本](components/tool-effects.md) | `src/uaw/tool/effects.py` |
| `tool.failure` | [失败恢复与等价切换](components/tool-failure.md) | `src/uaw/tool/failure.py` |
| `tool.mcp` | [MCP 连接与适配](components/tool-mcp.md) | `src/uaw/tool/mcp/facade.py` |
| `tool.adapters` | [领域与外部适配器](components/tool-adapters.md) | `src/uaw/tool/adapters.py` |
| `tool.results` | [结果规范化与分页](components/tool-results.md) | `src/uaw/tool/results.py` |
| `tool.audit` | [执行审计与指标](components/tool-audit.md) | `src/uaw/tool/audit.py` |
| `tool.invocation.schema` | [参数与可信上下文](components/tool-invocation-schema.md) | `src/uaw/tool/invocation/schema.py` |
| `tool.invocation.precheck` | [执行预检](components/tool-invocation-precheck.md) | `src/uaw/tool/invocation/precheck.py` |
| `tool.invocation.approval` | [必要审批等待](components/tool-invocation-approval.md) | `src/uaw/tool/invocation/approval.py` |
| `tool.invocation.recheck` | [执行前复核](components/tool-invocation-recheck.md) | `src/uaw/tool/invocation/recheck.py` |
| `tool.invocation.dispatch` | [意图登记与执行](components/tool-invocation-dispatch.md) | `src/uaw/tool/invocation/dispatch.py` |
| `tool.invocation.result` | [规范结果与结算](components/tool-invocation-result.md) | `src/uaw/tool/invocation/result.py` |
| `tool.mcp.provider` | [提供方绑定](components/tool-mcp-provider.md) | `src/uaw/tool/mcp/provider.py` |
| `tool.mcp.session` | [协议会话](components/tool-mcp-session.md) | `src/uaw/tool/mcp/session.py` |
| `tool.mcp.capabilities` | [能力规范化](components/tool-mcp-capabilities.md) | `src/uaw/tool/mcp/capabilities.py` |
| `tool.mcp.invoke` | [闸门后调用](components/tool-mcp-invoke.md) | `src/uaw/tool/mcp/invoke.py` |
| `tool.mcp.invalidate` | [变化与撤销](components/tool-mcp-invalidate.md) | `src/uaw/tool/mcp/invalidate.py` |

## 工作区 · Workspace

| 节点 | 开发策略文档 | 计划代码位置 |
| --- | --- | --- |
| `workspace` | [工作区 · Workspace](modules/workspace.md) | `src/uaw/workspace/facade.py` |
| `workspace.binding` | [项目绑定与本地授权](components/workspace-binding.md) | `src/uaw/workspace/binding.py` |
| `workspace.base` | [输入基础状态](components/workspace-base.md) | `src/uaw/workspace/base.py` |
| `workspace.isolation` | [隔离与分支](components/workspace-isolation.md) | `src/uaw/workspace/isolation.py` |
| `workspace.environment` | [环境准备与回收](components/workspace-environment.md) | `src/uaw/workspace/environment.py` |
| `workspace.process` | [文件与进程执行](components/workspace-process.md) | `src/uaw/workspace/process.py` |
| `workspace.changes` | [变更与冲突合并](components/workspace-changes.md) | `src/uaw/workspace/changes.py` |
| `workspace.artifacts` | [产物与格式适配](components/workspace-artifacts.md) | `src/uaw/workspace/artifacts.py` |
| `workspace.review` | [审阅与局部接受](components/workspace-review.md) | `src/uaw/workspace/review.py` |

## 模型调用 · Model

| 节点 | 开发策略文档 | 计划代码位置 |
| --- | --- | --- |
| `model` | [模型调用 · Model](modules/model.md) | `src/uaw/model/facade.py` |
| `model.catalog` | [可见模型目录](components/model-catalog.md) | `src/uaw/model/catalog.py` |
| `model.policy` | [选择与模型继承](components/model-policy.md) | `src/uaw/model/policy.py` |
| `model.capability` | [兼容与Auto选择](components/model-capability.md) | `src/uaw/model/capability.py` |
| `model.gateway` | [调用网关](components/model-gateway.md) | `src/uaw/model/gateway.py` |
| `model.adapters` | [供应商协议适配](components/model-adapters.md) | `src/uaw/model/adapters.py` |
| `model.recovery` | [调用恢复](components/model-recovery.md) | `src/uaw/model/recovery.py` |
| `model.usage` | [计量与版本记录](components/model-usage.md) | `src/uaw/model/usage.py` |

## 运行控制 · Run

| 节点 | 开发策略文档 | 计划代码位置 |
| --- | --- | --- |
| `run` | [运行控制 · Run](modules/run.md) | `src/uaw/run/facade.py` |
| `run.history` | [历史与输入权威](components/run-history.md) | `src/uaw/run/history.py` |
| `run.state` | [Run 与交互项](components/run-state.md) | `src/uaw/run/state.py` |
| `run.events` | [事件与重连](components/run-events.md) | `src/uaw/run/events.py` |
| `run.budget` | [预算与准入](components/run-budget.md) | `src/uaw/run/budget.py` |
| `run.approval` | [审批与用户控制](components/run-approval.md) | `src/uaw/run/approval.py` |
| `run.checkpoint` | [恢复边界与版本](components/run-checkpoint.md) | `src/uaw/run/checkpoint.py` |
| `run.resume` | [租约与执行恢复](components/run-resume.md) | `src/uaw/run/resume/facade.py` |
| `run.cancel` | [取消传播](components/run-cancel.md) | `src/uaw/run/cancel.py` |
| `run.trigger` | [未来触发器](components/run-trigger.md) | `src/uaw/run/trigger.py` |
| `run.resume.lease` | [取得运行租约](components/run-resume-lease.md) | `src/uaw/run/resume/lease.py` |
| `run.resume.versions` | [版本兼容检查](components/run-resume-versions.md) | `src/uaw/run/resume/versions.py` |
| `run.resume.access` | [重建连接与核验](components/run-resume-access.md) | `src/uaw/run/resume/access.py` |
| `run.resume.effects` | [Tool未决动作对账](components/run-resume-effects.md) | `src/uaw/run/resume/effects.py` |
| `run.resume.workspace` | [工作区实际版本](components/run-resume-workspace.md) | `src/uaw/run/resume/workspace.py` |
| `run.resume.continue` | [恢复可运行工作](components/run-resume-continue.md) | `src/uaw/run/resume/continue_run.py` |

## 共享支撑与控制层

| 节点 | 开发策略文档 | 计划代码位置 |
| --- | --- | --- |
| `support` | [共享支撑与控制层](modules/support.md) | `src/uaw/shared/__init__.py` |
| `support.configuration` | [配置与账号控制层](components/support-configuration.md) | `src/uaw/shared/configuration.py` |
| `support.extensions` | [扩展包与版本发布](components/support-extensions.md) | `src/uaw/shared/extensions.py` |
| `support.cache` | [共享缓存设施](components/support-cache.md) | `src/uaw/shared/cache.py` |
| `support.observability` | [运行观测](components/support-observability.md) | `src/uaw/shared/observability.py` |
| `support.evaluation` | [离线质量评测](components/support-evaluation.md) | `src/uaw/shared/evaluation.py` |
| `support.stores` | [存储适配与访问](components/support-stores.md) | `src/uaw/shared/stores.py` |

