# 架构节点 → 开发轮次覆盖

[开发计划](README.md) · [策略索引](../design/README.md)

115个节点均有计划关联。同一节点可在多个阶段完善；这里证明排入工作包，不证明全部功能已经实现。根节点聚合不把后续子能力算作早期完成。

| 节点与作用 | 实施/完善轮 | 策略/接口 | 目标代码 |
| --- | --- | --- | --- |
| `ui` · 交互页面 | [P1-10](rounds/P1-10.md)、[P2-08](rounds/P2-08.md)、[P4-09](rounds/P4-09.md)、[P5-05](rounds/P5-05.md) | [策略](../design/components/ui.md) / [接口](../api/nodes/ui.md) | `apps/web/src/features/workspace/` |
| `ingress` · 产品入口 | [P1-10](rounds/P1-10.md)、[P2-08](rounds/P2-08.md)、[P4-09](rounds/P4-09.md)、[P5-05](rounds/P5-05.md) | [策略](../design/components/ingress.md) / [接口](../api/nodes/ingress.md) | `src/uaw/api/ingress.py` |
| `intent` · 任务理解 · Intent | [P1-01](rounds/P1-01.md) | [策略](../design/modules/intent.md) / [接口](../api/nodes/intent.md) | `src/uaw/intent/facade.py` |
| `agent` · 决策执行 · Agent | [P1-07](rounds/P1-07.md) | [策略](../design/modules/agent.md) / [接口](../api/nodes/agent.md) | `src/uaw/agent/facade.py` |
| `context` · 上下文 · Context | [P1-02](rounds/P1-02.md) | [策略](../design/modules/context.md) / [接口](../api/nodes/context.md) | `src/uaw/context/facade.py` |
| `tool` · 工具执行 · Tool | [P1-03](rounds/P1-03.md) | [策略](../design/modules/tool.md) / [接口](../api/nodes/tool.md) | `src/uaw/tool/facade.py` |
| `workspace` · 工作区 · Workspace | [P1-04](rounds/P1-04.md) | [策略](../design/modules/workspace.md) / [接口](../api/nodes/workspace.md) | `src/uaw/workspace/facade.py` |
| `model` · 模型调用 · Model | [P0-05](rounds/P0-05.md) | [策略](../design/modules/model.md) / [接口](../api/nodes/model.md) | `src/uaw/model/facade.py` |
| `run` · 运行控制 · Run | [P0-04](rounds/P0-04.md) | [策略](../design/modules/run.md) / [接口](../api/nodes/run.md) | `src/uaw/run/facade.py` |
| `support` · 共享支撑与控制层 | [P0-01](rounds/P0-01.md) | [策略](../design/modules/support.md) / [接口](../api/nodes/support.md) | `src/uaw/shared/__init__.py` |
| `intent.preview` · 草稿理解预览 | [P4-09](rounds/P4-09.md) | [策略](../design/components/intent-preview.md) / [接口](../api/nodes/intent.preview.md) | `src/uaw/intent/preview.py` |
| `intent.original` · 原文读取 | [P1-01](rounds/P1-01.md) | [策略](../design/components/intent-original.md) / [接口](../api/nodes/intent.original.md) | `src/uaw/intent/original.py` |
| `intent.semantic` · 语义解析 | [P1-01](rounds/P1-01.md) | [策略](../design/components/intent-semantic.md) / [接口](../api/nodes/intent.semantic.md) | `src/uaw/intent/semantic.py` |
| `intent.references` · 指代解析 | [P3-01](rounds/P3-01.md) | [策略](../design/components/intent-references.md) / [接口](../api/nodes/intent.references.md) | `src/uaw/intent/references.py` |
| `intent.probe` · 必要信息探查 | [P3-01](rounds/P3-01.md) | [策略](../design/components/intent-probe.md) / [接口](../api/nodes/intent.probe.md) | `src/uaw/intent/probe.py` |
| `intent.ambiguity` · 歧义处理 | [P3-01](rounds/P3-01.md) | [策略](../design/components/intent-ambiguity.md) / [接口](../api/nodes/intent.ambiguity.md) | `src/uaw/intent/ambiguity.py` |
| `intent.frame` · 任务框架 | [P1-01](rounds/P1-01.md) | [策略](../design/components/intent-frame.md) / [接口](../api/nodes/intent.frame.md) | `src/uaw/intent/frame.py` |
| `agent.definitions` · 子Agent定义与发现 | [P2-04](rounds/P2-04.md) | [策略](../design/components/agent-definitions.md) / [接口](../api/nodes/agent.definitions.md) | `src/uaw/agent/definitions/facade.py` |
| `agent.loop` · Agent 决策循环 | [P1-07](rounds/P1-07.md) | [策略](../design/components/agent-loop.md) / [接口](../api/nodes/agent.loop.md) | `src/uaw/agent/loop.py` |
| `agent.assessment` · 按需执行评估 | [P3-01](rounds/P3-01.md) | [策略](../design/components/agent-assessment.md) / [接口](../api/nodes/agent.assessment.md) | `src/uaw/agent/assessment.py` |
| `agent.planning` · 规划与依赖校验 | [P3-01](rounds/P3-01.md)、[P3-02](rounds/P3-02.md)、[P3-07](rounds/P3-07.md) | [策略](../design/components/agent-planning.md) / [接口](../api/nodes/agent.planning.md) | `src/uaw/agent/planning.py` |
| `agent.scheduler` · 节点与资源调度 | [P3-02](rounds/P3-02.md) | [策略](../design/components/agent-scheduler.md) / [接口](../api/nodes/agent.scheduler.md) | `src/uaw/agent/scheduler.py` |
| `agent.collaboration` · 委派与控制权 | [P2-05](rounds/P2-05.md)、[P3-04](rounds/P3-04.md) | [策略](../design/components/agent-collaboration.md) / [接口](../api/nodes/agent.collaboration.md) | `src/uaw/agent/collaboration/facade.py` |
| `agent.skills` · 技能与任务模板 | [P2-03](rounds/P2-03.md)、[P2-07](rounds/P2-07.md) | [策略](../design/components/agent-skills.md) / [接口](../api/nodes/agent.skills.md) | `src/uaw/agent/skills.py` |
| `agent.completion` · 完成核验协调 | [P1-08](rounds/P1-08.md) | [策略](../design/components/agent-completion.md) / [接口](../api/nodes/agent.completion.md) | `src/uaw/agent/completion/facade.py` |
| `agent.board` · 共享任务板 | [P2-06](rounds/P2-06.md)、[P3-04](rounds/P3-04.md)、[P3-07](rounds/P3-07.md) | [策略](../design/components/agent-board.md) / [接口](../api/nodes/agent.board.md) | `src/uaw/agent/board.py` |
| `agent.factory` · 统一实例工厂 | [P1-07](rounds/P1-07.md)、[P2-05](rounds/P2-05.md)、[P3-04](rounds/P3-04.md) | [策略](../design/components/agent-factory.md) / [接口](../api/nodes/agent.factory.md) | `src/uaw/agent/factory.py` |
| `agent.definitions.designer` · 角色设计方法 | [P2-04](rounds/P2-04.md) | [策略](../design/components/agent-definitions-designer.md) / [接口](../api/nodes/agent.definitions.designer.md) | `src/uaw/agent/definitions/designer.py` |
| `agent.definitions.validator` · 定义与授权校验 | [P2-04](rounds/P2-04.md) | [策略](../design/components/agent-definitions-validator.md) / [接口](../api/nodes/agent.definitions.validator.md) | `src/uaw/agent/definitions/validator.py` |
| `agent.definitions.model_intent` · 模型意图解析 | [P2-04](rounds/P2-04.md)、[P4-08](rounds/P4-08.md) | [策略](../design/components/agent-definitions-model_intent.md) / [接口](../api/nodes/agent.definitions.model_intent.md) | `src/uaw/agent/definitions/model_intent.py` |
| `agent.definitions.repository` · 定义提交与版本 | [P2-04](rounds/P2-04.md) | [策略](../design/components/agent-definitions-repository.md) / [接口](../api/nodes/agent.definitions.repository.md) | `src/uaw/agent/definitions/repository.py` |
| `agent.definitions.discovery` · 会话Agent发现 | [P2-04](rounds/P2-04.md)、[P4-03](rounds/P4-03.md) | [策略](../design/components/agent-definitions-discovery.md) / [接口](../api/nodes/agent.definitions.discovery.md) | `src/uaw/agent/definitions/discovery.py` |
| `agent.definitions.change_service` · 配置变更与撤销 | [P2-04](rounds/P2-04.md)、[P3-06](rounds/P3-06.md) | [策略](../design/components/agent-definitions-change_service.md) / [接口](../api/nodes/agent.definitions.change_service.md) | `src/uaw/agent/definitions/change_service.py` |
| `context.sources` · 来源解析 | [P1-02](rounds/P1-02.md)、[P4-04](rounds/P4-04.md) | [策略](../design/components/context-sources.md) / [接口](../api/nodes/context.sources.md) | `src/uaw/context/sources.py` |
| `context.rules` · 规则与信任装配 | [P1-02](rounds/P1-02.md)、[P2-03](rounds/P2-03.md) | [策略](../design/components/context-rules.md) / [接口](../api/nodes/context.rules.md) | `src/uaw/context/rules.py` |
| `context.ingestion` · 摄取与索引发布 | [P2-01](rounds/P2-01.md) | [策略](../design/components/context-ingestion.md) / [接口](../api/nodes/context.ingestion.md) | `src/uaw/context/ingestion.py` |
| `context.retrieval` · 资料检索与证据 | [P2-01](rounds/P2-01.md)、[P4-03](rounds/P4-03.md)、[P4-04](rounds/P4-04.md) | [策略](../design/components/context-retrieval.md) / [接口](../api/nodes/context.retrieval.md) | `src/uaw/context/retrieval.py` |
| `context.memory` · 记忆生命周期 | [P4-01](rounds/P4-01.md) | [策略](../design/components/context-memory.md) / [接口](../api/nodes/context.memory.md) | `src/uaw/context/memory/facade.py` |
| `context.selection` · 选择与上下文预算 | [P1-02](rounds/P1-02.md)、[P4-02](rounds/P4-02.md) | [策略](../design/components/context-selection.md) / [接口](../api/nodes/context.selection.md) | `src/uaw/context/selection.py` |
| `context.compression` · 压缩与关键项保护 | [P4-02](rounds/P4-02.md) | [策略](../design/components/context-compression.md) / [接口](../api/nodes/context.compression.md) | `src/uaw/context/compression.py` |
| `context.composer` · 装配与快照 | [P1-02](rounds/P1-02.md)、[P4-02](rounds/P4-02.md) | [策略](../design/components/context-composer.md) / [接口](../api/nodes/context.composer.md) | `src/uaw/context/composer.py` |
| `context.references` · 引用登记与解析 | [P1-02](rounds/P1-02.md)、[P2-02](rounds/P2-02.md)、[P2-07](rounds/P2-07.md) | [策略](../design/components/context-references.md) / [接口](../api/nodes/context.references.md) | `src/uaw/context/references.py` |
| `tool.registry` · 工具注册与版本 | [P1-03](rounds/P1-03.md)、[P4-03](rounds/P4-03.md) | [策略](../design/components/tool-registry.md) / [接口](../api/nodes/tool.registry.md) | `src/uaw/tool/registry.py` |
| `tool.discovery` · 工具发现与筛选 | [P1-03](rounds/P1-03.md)、[P4-03](rounds/P4-03.md) | [策略](../design/components/tool-discovery.md) / [接口](../api/nodes/tool.discovery.md) | `src/uaw/tool/discovery.py` |
| `tool.invocation` · 调用闸门与派发 | [P1-03](rounds/P1-03.md)、[P3-03](rounds/P3-03.md) | [策略](../design/components/tool-invocation.md) / [接口](../api/nodes/tool.invocation.md) | `src/uaw/tool/invocation/facade.py` |
| `tool.effects` · 调用与副作用账本 | [P1-03](rounds/P1-03.md)、[P3-03](rounds/P3-03.md)、[P5-02](rounds/P5-02.md) | [策略](../design/components/tool-effects.md) / [接口](../api/nodes/tool.effects.md) | `src/uaw/tool/effects.py` |
| `tool.failure` · 失败恢复与等价切换 | [P1-03](rounds/P1-03.md)、[P4-05](rounds/P4-05.md) | [策略](../design/components/tool-failure.md) / [接口](../api/nodes/tool.failure.md) | `src/uaw/tool/failure.py` |
| `tool.mcp` · MCP 连接与适配 | [P4-05](rounds/P4-05.md) | [策略](../design/components/tool-mcp.md) / [接口](../api/nodes/tool.mcp.md) | `src/uaw/tool/mcp/facade.py` |
| `tool.adapters` · 领域与外部适配器 | [P1-03](rounds/P1-03.md)、[P2-02](rounds/P2-02.md) | [策略](../design/components/tool-adapters.md) / [接口](../api/nodes/tool.adapters.md) | `src/uaw/tool/adapters.py` |
| `tool.results` · 结果规范化与分页 | [P1-03](rounds/P1-03.md)、[P2-02](rounds/P2-02.md) | [策略](../design/components/tool-results.md) / [接口](../api/nodes/tool.results.md) | `src/uaw/tool/results.py` |
| `tool.audit` · 执行审计与指标 | [P1-03](rounds/P1-03.md) | [策略](../design/components/tool-audit.md) / [接口](../api/nodes/tool.audit.md) | `src/uaw/tool/audit.py` |
| `workspace.binding` · 项目绑定与本地授权 | [P1-04](rounds/P1-04.md)、[P5-05](rounds/P5-05.md) | [策略](../design/components/workspace-binding.md) / [接口](../api/nodes/workspace.binding.md) | `src/uaw/workspace/binding.py` |
| `workspace.base` · 输入基础状态 | [P1-05](rounds/P1-05.md)、[P3-05](rounds/P3-05.md) | [策略](../design/components/workspace-base.md) / [接口](../api/nodes/workspace.base.md) | `src/uaw/workspace/base.py` |
| `workspace.isolation` · 隔离与分支 | [P1-05](rounds/P1-05.md)、[P3-05](rounds/P3-05.md)、[P4-07](rounds/P4-07.md) | [策略](../design/components/workspace-isolation.md) / [接口](../api/nodes/workspace.isolation.md) | `src/uaw/workspace/isolation.py` |
| `workspace.environment` · 环境准备与回收 | [P1-05](rounds/P1-05.md)、[P4-07](rounds/P4-07.md) | [策略](../design/components/workspace-environment.md) / [接口](../api/nodes/workspace.environment.md) | `src/uaw/workspace/environment.py` |
| `workspace.process` · 文件与进程执行 | [P1-05](rounds/P1-05.md)、[P4-07](rounds/P4-07.md) | [策略](../design/components/workspace-process.md) / [接口](../api/nodes/workspace.process.md) | `src/uaw/workspace/process.py` |
| `workspace.changes` · 变更与冲突合并 | [P1-06](rounds/P1-06.md)、[P3-05](rounds/P3-05.md)、[P3-06](rounds/P3-06.md) | [策略](../design/components/workspace-changes.md) / [接口](../api/nodes/workspace.changes.md) | `src/uaw/workspace/changes.py` |
| `workspace.artifacts` · 产物与格式适配 | [P1-06](rounds/P1-06.md)、[P3-06](rounds/P3-06.md) | [策略](../design/components/workspace-artifacts.md) / [接口](../api/nodes/workspace.artifacts.md) | `src/uaw/workspace/artifacts.py` |
| `workspace.review` · 审阅与局部接受 | [P1-06](rounds/P1-06.md)、[P3-06](rounds/P3-06.md) | [策略](../design/components/workspace-review.md) / [接口](../api/nodes/workspace.review.md) | `src/uaw/workspace/review.py` |
| `model.catalog` · 可见模型目录 | [P0-05](rounds/P0-05.md)、[P4-08](rounds/P4-08.md) | [策略](../design/components/model-catalog.md) / [接口](../api/nodes/model.catalog.md) | `src/uaw/model/catalog.py` |
| `model.policy` · 选择与模型继承 | [P0-05](rounds/P0-05.md)、[P4-08](rounds/P4-08.md) | [策略](../design/components/model-policy.md) / [接口](../api/nodes/model.policy.md) | `src/uaw/model/policy.py` |
| `model.capability` · 兼容与Auto选择 | [P0-05](rounds/P0-05.md)、[P4-08](rounds/P4-08.md) | [策略](../design/components/model-capability.md) / [接口](../api/nodes/model.capability.md) | `src/uaw/model/capability.py` |
| `model.gateway` · 调用网关 | [P0-05](rounds/P0-05.md) | [策略](../design/components/model-gateway.md) / [接口](../api/nodes/model.gateway.md) | `src/uaw/model/gateway.py` |
| `model.adapters` · 供应商协议适配 | [P0-05](rounds/P0-05.md) | [策略](../design/components/model-adapters.md) / [接口](../api/nodes/model.adapters.md) | `src/uaw/model/adapters.py` |
| `model.recovery` · 调用恢复 | [P0-05](rounds/P0-05.md)、[P4-08](rounds/P4-08.md) | [策略](../design/components/model-recovery.md) / [接口](../api/nodes/model.recovery.md) | `src/uaw/model/recovery.py` |
| `model.usage` · 计量与版本记录 | [P0-05](rounds/P0-05.md)、[P4-04](rounds/P4-04.md)、[P4-08](rounds/P4-08.md) | [策略](../design/components/model-usage.md) / [接口](../api/nodes/model.usage.md) | `src/uaw/model/usage.py` |
| `run.history` · 历史与输入权威 | [P0-04](rounds/P0-04.md)、[P3-07](rounds/P3-07.md) | [策略](../design/components/run-history.md) / [接口](../api/nodes/run.history.md) | `src/uaw/run/history.py` |
| `run.state` · Run 与交互项 | [P0-04](rounds/P0-04.md)、[P3-07](rounds/P3-07.md)、[P5-01](rounds/P5-01.md) | [策略](../design/components/run-state.md) / [接口](../api/nodes/run.state.md) | `src/uaw/run/state.py` |
| `run.events` · 事件与重连 | [P0-04](rounds/P0-04.md)、[P5-01](rounds/P5-01.md) | [策略](../design/components/run-events.md) / [接口](../api/nodes/run.events.md) | `src/uaw/run/events.py` |
| `run.budget` · 预算与准入 | [P0-04](rounds/P0-04.md)、[P3-03](rounds/P3-03.md)、[P5-01](rounds/P5-01.md) | [策略](../design/components/run-budget.md) / [接口](../api/nodes/run.budget.md) | `src/uaw/run/budget.py` |
| `run.approval` · 审批与用户控制 | [P1-09](rounds/P1-09.md)、[P3-07](rounds/P3-07.md)、[P4-09](rounds/P4-09.md) | [策略](../design/components/run-approval.md) / [接口](../api/nodes/run.approval.md) | `src/uaw/run/approval.py` |
| `run.checkpoint` · 恢复边界与版本 | [P5-01](rounds/P5-01.md) | [策略](../design/components/run-checkpoint.md) / [接口](../api/nodes/run.checkpoint.md) | `src/uaw/run/checkpoint.py` |
| `run.resume` · 租约与执行恢复 | [P5-02](rounds/P5-02.md) | [策略](../design/components/run-resume.md) / [接口](../api/nodes/run.resume.md) | `src/uaw/run/resume/facade.py` |
| `run.cancel` · 取消传播 | [P1-09](rounds/P1-09.md)、[P3-07](rounds/P3-07.md)、[P5-02](rounds/P5-02.md) | [策略](../design/components/run-cancel.md) / [接口](../api/nodes/run.cancel.md) | `src/uaw/run/cancel.py` |
| `run.trigger` · 未来触发器 | [P5-04](rounds/P5-04.md) | [策略](../design/components/run-trigger.md) / [接口](../api/nodes/run.trigger.md) | `src/uaw/run/trigger.py` |
| `support.configuration` · 配置与账号控制层 | [P0-03](rounds/P0-03.md)、[P4-05](rounds/P4-05.md)、[P4-06](rounds/P4-06.md)、[P5-03](rounds/P5-03.md)、[P5-05](rounds/P5-05.md) | [策略](../design/components/support-configuration.md) / [接口](../api/nodes/support.configuration.md) | `src/uaw/shared/configuration.py` |
| `support.extensions` · 扩展包与版本发布 | [P4-06](rounds/P4-06.md) | [策略](../design/components/support-extensions.md) / [接口](../api/nodes/support.extensions.md) | `src/uaw/shared/extensions.py` |
| `support.cache` · 共享缓存设施 | [P4-04](rounds/P4-04.md) | [策略](../design/components/support-cache.md) / [接口](../api/nodes/support.cache.md) | `src/uaw/shared/cache.py` |
| `support.observability` · 运行观测 | [P0-04](rounds/P0-04.md)、[P5-03](rounds/P5-03.md) | [策略](../design/components/support-observability.md) / [接口](../api/nodes/support.observability.md) | `src/uaw/shared/observability.py` |
| `support.evaluation` · 离线质量评测 | [P5-03](rounds/P5-03.md) | [策略](../design/components/support-evaluation.md) / [接口](../api/nodes/support.evaluation.md) | `src/uaw/shared/evaluation.py` |
| `support.stores` · 存储适配与访问 | [P0-02](rounds/P0-02.md) | [策略](../design/components/support-stores.md) / [接口](../api/nodes/support.stores.md) | `src/uaw/shared/stores.py` |
| `tool.invocation.schema` · 参数与可信上下文 | [P1-03](rounds/P1-03.md) | [策略](../design/components/tool-invocation-schema.md) / [接口](../api/nodes/tool.invocation.schema.md) | `src/uaw/tool/invocation/schema.py` |
| `tool.invocation.precheck` · 执行预检 | [P1-03](rounds/P1-03.md) | [策略](../design/components/tool-invocation-precheck.md) / [接口](../api/nodes/tool.invocation.precheck.md) | `src/uaw/tool/invocation/precheck.py` |
| `tool.invocation.approval` · 必要审批等待 | [P1-03](rounds/P1-03.md) | [策略](../design/components/tool-invocation-approval.md) / [接口](../api/nodes/tool.invocation.approval.md) | `src/uaw/tool/invocation/approval.py` |
| `tool.invocation.recheck` · 执行前复核 | [P1-03](rounds/P1-03.md) | [策略](../design/components/tool-invocation-recheck.md) / [接口](../api/nodes/tool.invocation.recheck.md) | `src/uaw/tool/invocation/recheck.py` |
| `tool.invocation.dispatch` · 意图登记与执行 | [P1-03](rounds/P1-03.md) | [策略](../design/components/tool-invocation-dispatch.md) / [接口](../api/nodes/tool.invocation.dispatch.md) | `src/uaw/tool/invocation/dispatch.py` |
| `tool.invocation.result` · 规范结果与结算 | [P1-03](rounds/P1-03.md) | [策略](../design/components/tool-invocation-result.md) / [接口](../api/nodes/tool.invocation.result.md) | `src/uaw/tool/invocation/result.py` |
| `agent.collaboration.contract` · 子任务契约 | [P2-05](rounds/P2-05.md) | [策略](../design/components/agent-collaboration-contract.md) / [接口](../api/nodes/agent.collaboration.contract.md) | `src/uaw/agent/collaboration/contract.py` |
| `agent.collaboration.instance` · 隔离运行实例 | [P2-05](rounds/P2-05.md)、[P3-04](rounds/P3-04.md) | [策略](../design/components/agent-collaboration-instance.md) / [接口](../api/nodes/agent.collaboration.instance.md) | `src/uaw/agent/collaboration/instance.py` |
| `agent.collaboration.channel` · 消息与受控引用 | [P2-05](rounds/P2-05.md)、[P3-04](rounds/P3-04.md) | [策略](../design/components/agent-collaboration-channel.md) / [接口](../api/nodes/agent.collaboration.channel.md) | `src/uaw/agent/collaboration/channel.py` |
| `agent.collaboration.join` · 结果核验与汇总 | [P2-06](rounds/P2-06.md)、[P3-04](rounds/P3-04.md) | [策略](../design/components/agent-collaboration-join.md) / [接口](../api/nodes/agent.collaboration.join.md) | `src/uaw/agent/collaboration/join.py` |
| `agent.collaboration.handoff` · 可选控制权交接 | [P5-04](rounds/P5-04.md) | [策略](../design/components/agent-collaboration-handoff.md) / [接口](../api/nodes/agent.collaboration.handoff.md) | `src/uaw/agent/collaboration/handoff.py` |
| `agent.collaboration.cancel` · 生命周期与取消 | [P2-05](rounds/P2-05.md)、[P3-04](rounds/P3-04.md) | [策略](../design/components/agent-collaboration-cancel.md) / [接口](../api/nodes/agent.collaboration.cancel.md) | `src/uaw/agent/collaboration/cancel.py` |
| `agent.completion.contract` · 语义交付契约 | [P1-08](rounds/P1-08.md) | [策略](../design/components/agent-completion-contract.md) / [接口](../api/nodes/agent.completion.contract.md) | `src/uaw/agent/completion/contract.py` |
| `agent.completion.evidence` · 真实证据收集 | [P1-08](rounds/P1-08.md) | [策略](../design/components/agent-completion-evidence.md) / [接口](../api/nodes/agent.completion.evidence.md) | `src/uaw/agent/completion/evidence.py` |
| `agent.completion.semantic` · 语义核对 | [P1-08](rounds/P1-08.md)、[P2-07](rounds/P2-07.md) | [策略](../design/components/agent-completion-semantic.md) / [接口](../api/nodes/agent.completion.semantic.md) | `src/uaw/agent/completion/semantic.py` |
| `agent.completion.version` · 版本与硬条件校验 | [P1-08](rounds/P1-08.md)、[P3-06](rounds/P3-06.md) | [策略](../design/components/agent-completion-version.md) / [接口](../api/nodes/agent.completion.version.md) | `src/uaw/agent/completion/version.py` |
| `agent.completion.delivery` · 提交交付 | [P1-08](rounds/P1-08.md) | [策略](../design/components/agent-completion-delivery.md) / [接口](../api/nodes/agent.completion.delivery.md) | `src/uaw/agent/completion/delivery.py` |
| `agent.completion.acceptance` · 用户接受与迭代 | [P1-08](rounds/P1-08.md) | [策略](../design/components/agent-completion-acceptance.md) / [接口](../api/nodes/agent.completion.acceptance.md) | `src/uaw/agent/completion/acceptance.py` |
| `context.memory.candidate` · 记忆候选 | [P4-01](rounds/P4-01.md) | [策略](../design/components/context-memory-candidate.md) / [接口](../api/nodes/context.memory.candidate.md) | `src/uaw/context/memory/candidate.py` |
| `context.memory.policy` · 范围与写入政策 | [P4-01](rounds/P4-01.md) | [策略](../design/components/context-memory-policy.md) / [接口](../api/nodes/context.memory.policy.md) | `src/uaw/context/memory/policy.py` |
| `context.memory.conflict` · 查重与冲突 | [P4-01](rounds/P4-01.md) | [策略](../design/components/context-memory-conflict.md) / [接口](../api/nodes/context.memory.conflict.md) | `src/uaw/context/memory/conflict.py` |
| `context.memory.store` · 提交与召回 | [P4-01](rounds/P4-01.md) | [策略](../design/components/context-memory-store.md) / [接口](../api/nodes/context.memory.store.md) | `src/uaw/context/memory/store.py` |
| `context.memory.forget` · 遗忘与删除传播 | [P4-01](rounds/P4-01.md) | [策略](../design/components/context-memory-forget.md) / [接口](../api/nodes/context.memory.forget.md) | `src/uaw/context/memory/forget.py` |
| `tool.mcp.provider` · 提供方绑定 | [P4-05](rounds/P4-05.md) | [策略](../design/components/tool-mcp-provider.md) / [接口](../api/nodes/tool.mcp.provider.md) | `src/uaw/tool/mcp/provider.py` |
| `tool.mcp.session` · 协议会话 | [P4-05](rounds/P4-05.md) | [策略](../design/components/tool-mcp-session.md) / [接口](../api/nodes/tool.mcp.session.md) | `src/uaw/tool/mcp/session.py` |
| `tool.mcp.capabilities` · 能力规范化 | [P4-05](rounds/P4-05.md) | [策略](../design/components/tool-mcp-capabilities.md) / [接口](../api/nodes/tool.mcp.capabilities.md) | `src/uaw/tool/mcp/capabilities.py` |
| `tool.mcp.invoke` · 闸门后调用 | [P4-05](rounds/P4-05.md) | [策略](../design/components/tool-mcp-invoke.md) / [接口](../api/nodes/tool.mcp.invoke.md) | `src/uaw/tool/mcp/invoke.py` |
| `tool.mcp.invalidate` · 变化与撤销 | [P4-05](rounds/P4-05.md) | [策略](../design/components/tool-mcp-invalidate.md) / [接口](../api/nodes/tool.mcp.invalidate.md) | `src/uaw/tool/mcp/invalidate.py` |
| `run.resume.lease` · 取得运行租约 | [P5-02](rounds/P5-02.md) | [策略](../design/components/run-resume-lease.md) / [接口](../api/nodes/run.resume.lease.md) | `src/uaw/run/resume/lease.py` |
| `run.resume.versions` · 版本兼容检查 | [P5-02](rounds/P5-02.md) | [策略](../design/components/run-resume-versions.md) / [接口](../api/nodes/run.resume.versions.md) | `src/uaw/run/resume/versions.py` |
| `run.resume.access` · 重建连接与核验 | [P5-02](rounds/P5-02.md) | [策略](../design/components/run-resume-access.md) / [接口](../api/nodes/run.resume.access.md) | `src/uaw/run/resume/access.py` |
| `run.resume.effects` · Tool未决动作对账 | [P5-02](rounds/P5-02.md) | [策略](../design/components/run-resume-effects.md) / [接口](../api/nodes/run.resume.effects.md) | `src/uaw/run/resume/effects.py` |
| `run.resume.workspace` · 工作区实际版本 | [P5-02](rounds/P5-02.md) | [策略](../design/components/run-resume-workspace.md) / [接口](../api/nodes/run.resume.workspace.md) | `src/uaw/run/resume/workspace.py` |
| `run.resume.continue` · 恢复可运行工作 | [P5-02](rounds/P5-02.md) | [策略](../design/components/run-resume-continue.md) / [接口](../api/nodes/run.resume.continue.md) | `src/uaw/run/resume/continue_run.py` |

每个节点完成状态最终应细分实际支持的分支、默认关闭的扩展、未选后端和未通过案例。机器映射只有rounds和相关文档，不生成implemented=true。

