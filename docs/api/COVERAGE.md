# 架构节点与接口覆盖

[接口总入口](README.md)。覆盖表示节点已有契约，不能代替Runtime实现/联调验收。

## ui · 交互页面

[详细开发设计](../../docs/design/components/ui.md) · 计划位置：`apps/web/src/features/workspace/`。

- [http · conversations.create](interfaces/http--conversations-create.md)
- [http · conversations.list](interfaces/http--conversations-list.md)
- [http · conversations.get](interfaces/http--conversations-get.md)
- [http · conversations.configure](interfaces/http--conversations-configure.md)
- [http · conversations.items](interfaces/http--conversations-items.md)
- [http · intent.preview](interfaces/http--intent-preview.md)
- [http · turns.submit](interfaces/http--turns-submit.md)
- [http · tasks.get](interfaces/http--tasks-get.md)
- [http · tasks.frame](interfaces/http--tasks-frame.md)
- [http · tasks.plan](interfaces/http--tasks-plan.md)
- [http · tasks.board](interfaces/http--tasks-board.md)
- [http · runs.get](interfaces/http--runs-get.md)
- [http · runs.control](interfaces/http--runs-control.md)
- [http · runs.resume](interfaces/http--runs-resume.md)
- [http · events.stream](interfaces/http--events-stream.md)
- [http · approvals.get](interfaces/http--approvals-get.md)
- [http · approvals.decide](interfaces/http--approvals-decide.md)
- [http · assets.upload.begin](interfaces/http--assets-upload-begin.md)
- [http · definitions.create](interfaces/http--definitions-create.md)
- [http · definitions.list](interfaces/http--definitions-list.md)
- [http · agents.get](interfaces/http--agents-get.md)
- [http · agents.cancel](interfaces/http--agents-cancel.md)
- [http · projects.list](interfaces/http--projects-list.md)
- [http · projects.bind](interfaces/http--projects-bind.md)
- [http · workspaces.changes](interfaces/http--workspaces-changes.md)
- [http · workspaces.revert](interfaces/http--workspaces-revert.md)
- [http · processes.get](interfaces/http--processes-get.md)
- [http · artifacts.list](interfaces/http--artifacts-list.md)
- [http · artifacts.get](interfaces/http--artifacts-get.md)
- [http · artifacts.preview](interfaces/http--artifacts-preview.md)
- [http · reviews.get](interfaces/http--reviews-get.md)
- [http · reviews.decide](interfaces/http--reviews-decide.md)
- [http · verification.get](interfaces/http--verification-get.md)
- [http · models.list](interfaces/http--models-list.md)
- [component · ui](interfaces/component--ui.md)

## ingress · 产品入口

[详细开发设计](../../docs/design/components/ingress.md) · 计划位置：`src/uaw/api/ingress.py`。

- [http · conversations.create](interfaces/http--conversations-create.md)
- [http · intent.preview](interfaces/http--intent-preview.md)
- [http · turns.submit](interfaces/http--turns-submit.md)
- [http · events.read](interfaces/http--events-read.md)
- [http · events.stream](interfaces/http--events-stream.md)
- [component · ingress](interfaces/component--ingress.md)

## intent · 任务理解 · Intent

[详细开发设计](../../docs/design/modules/intent.md) · 计划位置：`src/uaw/intent/facade.py`。

- [runtime · IntentRuntime.preview](interfaces/runtime--IntentRuntime-preview.md)
- [runtime · IntentRuntime.understand](interfaces/runtime--IntentRuntime-understand.md)
- [runtime · IntentRuntime.revise](interfaces/runtime--IntentRuntime-revise.md)

## agent · 决策执行 · Agent

[详细开发设计](../../docs/design/modules/agent.md) · 计划位置：`src/uaw/agent/facade.py`。

- [runtime · AgentRuntime.define_agent](interfaces/runtime--AgentRuntime-define-agent.md)
- [runtime · AgentRuntime.start](interfaces/runtime--AgentRuntime-start.md)
- [runtime · AgentRuntime.step](interfaces/runtime--AgentRuntime-step.md)
- [runtime · AgentRuntime.delegate](interfaces/runtime--AgentRuntime-delegate.md)
- [runtime · AgentRuntime.verify](interfaces/runtime--AgentRuntime-verify.md)

## context · 上下文 · Context

[详细开发设计](../../docs/design/modules/context.md) · 计划位置：`src/uaw/context/facade.py`。

- [runtime · ContextRuntime.build](interfaces/runtime--ContextRuntime-build.md)
- [runtime · ContextRuntime.ingest](interfaces/runtime--ContextRuntime-ingest.md)
- [runtime · ContextRuntime.remember](interfaces/runtime--ContextRuntime-remember.md)
- [runtime · ContextRuntime.recall](interfaces/runtime--ContextRuntime-recall.md)
- [runtime · ContextRuntime.forget](interfaces/runtime--ContextRuntime-forget.md)
- [runtime · ContextRuntime.resolve_reference](interfaces/runtime--ContextRuntime-resolve-reference.md)

## tool · 工具执行 · Tool

[详细开发设计](../../docs/design/modules/tool.md) · 计划位置：`src/uaw/tool/facade.py`。

- [runtime · ToolRuntime.discover](interfaces/runtime--ToolRuntime-discover.md)
- [runtime · ToolRuntime.invoke](interfaces/runtime--ToolRuntime-invoke.md)
- [runtime · ToolRuntime.reconcile](interfaces/runtime--ToolRuntime-reconcile.md)

## workspace · 工作区 · Workspace

[详细开发设计](../../docs/design/modules/workspace.md) · 计划位置：`src/uaw/workspace/facade.py`。

- [runtime · WorkspaceRuntime.allocate](interfaces/runtime--WorkspaceRuntime-allocate.md)
- [runtime · WorkspaceRuntime.prepare](interfaces/runtime--WorkspaceRuntime-prepare.md)
- [runtime · WorkspaceRuntime.merge](interfaces/runtime--WorkspaceRuntime-merge.md)
- [runtime · WorkspaceRuntime.revert](interfaces/runtime--WorkspaceRuntime-revert.md)
- [runtime · WorkspaceRuntime.review](interfaces/runtime--WorkspaceRuntime-review.md)

## model · 模型调用 · Model

[详细开发设计](../../docs/design/modules/model.md) · 计划位置：`src/uaw/model/facade.py`。

- [runtime · ModelRuntime.resolve_policy](interfaces/runtime--ModelRuntime-resolve-policy.md)
- [runtime · ModelRuntime.list](interfaces/runtime--ModelRuntime-list.md)
- [runtime · ModelRuntime.generate](interfaces/runtime--ModelRuntime-generate.md)

## run · 运行控制 · Run

[详细开发设计](../../docs/design/modules/run.md) · 计划位置：`src/uaw/run/facade.py`。

- [runtime · RunRuntime.create](interfaces/runtime--RunRuntime-create.md)
- [runtime · RunRuntime.control](interfaces/runtime--RunRuntime-control.md)
- [runtime · RunRuntime.checkpoint](interfaces/runtime--RunRuntime-checkpoint.md)
- [runtime · RunRuntime.resume](interfaces/runtime--RunRuntime-resume.md)

## support · 共享支撑与控制层

[详细开发设计](../../docs/design/modules/support.md) · 计划位置：`src/uaw/shared/__init__.py`。

- [http · connections.list](interfaces/http--connections-list.md)
- [http · connections.begin](interfaces/http--connections-begin.md)
- [http · connections.revoke](interfaces/http--connections-revoke.md)
- [http · admin.configuration.get](interfaces/http--admin-configuration-get.md)
- [http · admin.configuration.stage](interfaces/http--admin-configuration-stage.md)
- [http · admin.configuration.validate](interfaces/http--admin-configuration-validate.md)
- [http · admin.configuration.activate](interfaces/http--admin-configuration-activate.md)
- [http · admin.providers.configure](interfaces/http--admin-providers-configure.md)
- [http · admin.secrets.put](interfaces/http--admin-secrets-put.md)
- [http · admin.policies.register](interfaces/http--admin-policies-register.md)
- [http · admin.providers.revoke](interfaces/http--admin-providers-revoke.md)
- [component · support.configuration](interfaces/component--support-configuration.md)
- [http · skills.list](interfaces/http--skills-list.md)
- [http · admin.extensions.install](interfaces/http--admin-extensions-install.md)
- [http · admin.extensions.activate](interfaces/http--admin-extensions-activate.md)
- [http · admin.extensions.revoke](interfaces/http--admin-extensions-revoke.md)
- [http · admin.extensions.validate](interfaces/http--admin-extensions-validate.md)
- [http · admin.extensions.rollback](interfaces/http--admin-extensions-rollback.md)
- [component · support.extensions](interfaces/component--support-extensions.md)
- [http · sources.delete](interfaces/http--sources-delete.md)
- [http · memory.forget](interfaces/http--memory-forget.md)
- [http · admin.policies.register](interfaces/http--admin-policies-register.md)
- [component · support.cache](interfaces/component--support-cache.md)
- [http · admin.traces.list](interfaces/http--admin-traces-list.md)
- [component · support.observability](interfaces/component--support-observability.md)
- [http · admin.evaluations.run](interfaces/http--admin-evaluations-run.md)
- [http · admin.evaluations.get](interfaces/http--admin-evaluations-get.md)
- [component · support.evaluation](interfaces/component--support-evaluation.md)
- [component · support.stores](interfaces/component--support-stores.md)

## intent.preview · 草稿理解预览

[详细开发设计](../../docs/design/components/intent-preview.md) · 计划位置：`src/uaw/intent/preview.py`。

- [http · intent.preview](interfaces/http--intent-preview.md)
- [runtime · IntentRuntime.preview](interfaces/runtime--IntentRuntime-preview.md)
- [component · intent.preview](interfaces/component--intent-preview.md)

## intent.original · 原文读取

[详细开发设计](../../docs/design/components/intent-original.md) · 计划位置：`src/uaw/intent/original.py`。

- [http · turns.submit](interfaces/http--turns-submit.md)
- [runtime · IntentRuntime.understand](interfaces/runtime--IntentRuntime-understand.md)
- [component · intent.original](interfaces/component--intent-original.md)

## intent.semantic · 语义解析

[详细开发设计](../../docs/design/components/intent-semantic.md) · 计划位置：`src/uaw/intent/semantic.py`。

- [http · turns.submit](interfaces/http--turns-submit.md)
- [runtime · IntentRuntime.understand](interfaces/runtime--IntentRuntime-understand.md)
- [component · intent.semantic](interfaces/component--intent-semantic.md)

## intent.references · 指代解析

[详细开发设计](../../docs/design/components/intent-references.md) · 计划位置：`src/uaw/intent/references.py`。

- [component · intent.references](interfaces/component--intent-references.md)

## intent.probe · 必要信息探查

[详细开发设计](../../docs/design/components/intent-probe.md) · 计划位置：`src/uaw/intent/probe.py`。

- [component · intent.probe](interfaces/component--intent-probe.md)

## intent.ambiguity · 歧义处理

[详细开发设计](../../docs/design/components/intent-ambiguity.md) · 计划位置：`src/uaw/intent/ambiguity.py`。

- [tool · interaction.ask_user](interfaces/tool--interaction-ask-user.md)
- [component · intent.ambiguity](interfaces/component--intent-ambiguity.md)

## intent.frame · 任务框架

[详细开发设计](../../docs/design/components/intent-frame.md) · 计划位置：`src/uaw/intent/frame.py`。

- [http · turns.submit](interfaces/http--turns-submit.md)
- [http · tasks.frame](interfaces/http--tasks-frame.md)
- [http · runs.control](interfaces/http--runs-control.md)
- [runtime · IntentRuntime.understand](interfaces/runtime--IntentRuntime-understand.md)
- [runtime · IntentRuntime.revise](interfaces/runtime--IntentRuntime-revise.md)
- [component · intent.frame](interfaces/component--intent-frame.md)

## agent.definitions · 子Agent定义与发现

[详细开发设计](../../docs/design/components/agent-definitions.md) · 计划位置：`src/uaw/agent/definitions/facade.py`。

- [http · definitions.create](interfaces/http--definitions-create.md)
- [tool · agents.create](interfaces/tool--agents-create.md)
- [runtime · AgentRuntime.define_agent](interfaces/runtime--AgentRuntime-define-agent.md)
- [component · agent.definitions](interfaces/component--agent-definitions.md)

## agent.loop · Agent 决策循环

[详细开发设计](../../docs/design/components/agent-loop.md) · 计划位置：`src/uaw/agent/loop.py`。

- [http · turns.submit](interfaces/http--turns-submit.md)
- [http · agents.get](interfaces/http--agents-get.md)
- [runtime · AgentRuntime.step](interfaces/runtime--AgentRuntime-step.md)
- [component · agent.loop](interfaces/component--agent-loop.md)

## agent.assessment · 按需执行评估

[详细开发设计](../../docs/design/components/agent-assessment.md) · 计划位置：`src/uaw/agent/assessment.py`。

- [tool · agents.invoke](interfaces/tool--agents-invoke.md)
- [tool · tasks.assess](interfaces/tool--tasks-assess.md)
- [component · agent.assessment](interfaces/component--agent-assessment.md)

## agent.planning · 规划与依赖校验

[详细开发设计](../../docs/design/components/agent-planning.md) · 计划位置：`src/uaw/agent/planning.py`。

- [http · tasks.plan](interfaces/http--tasks-plan.md)
- [http · runs.control](interfaces/http--runs-control.md)
- [tool · tasks.plan](interfaces/tool--tasks-plan.md)
- [component · agent.planning](interfaces/component--agent-planning.md)

## agent.scheduler · 节点与资源调度

[详细开发设计](../../docs/design/components/agent-scheduler.md) · 计划位置：`src/uaw/agent/scheduler.py`。

- [tool · tasks.plan](interfaces/tool--tasks-plan.md)
- [component · agent.scheduler](interfaces/component--agent-scheduler.md)

## agent.collaboration · 委派与控制权

[详细开发设计](../../docs/design/components/agent-collaboration.md) · 计划位置：`src/uaw/agent/collaboration/facade.py`。

- [runtime · AgentRuntime.delegate](interfaces/runtime--AgentRuntime-delegate.md)
- [component · agent.collaboration](interfaces/component--agent-collaboration.md)

## agent.skills · 技能与任务模板

[详细开发设计](../../docs/design/components/agent-skills.md) · 计划位置：`src/uaw/agent/skills.py`。

- [http · skills.list](interfaces/http--skills-list.md)
- [tool · skills.load](interfaces/tool--skills-load.md)
- [component · agent.skills](interfaces/component--agent-skills.md)

## agent.completion · 完成核验协调

[详细开发设计](../../docs/design/components/agent-completion.md) · 计划位置：`src/uaw/agent/completion/facade.py`。

- [runtime · AgentRuntime.verify](interfaces/runtime--AgentRuntime-verify.md)
- [component · agent.completion](interfaces/component--agent-completion.md)

## agent.board · 共享任务板

[详细开发设计](../../docs/design/components/agent-board.md) · 计划位置：`src/uaw/agent/board.py`。

- [http · tasks.board](interfaces/http--tasks-board.md)
- [http · tasks.attach_conversation](interfaces/http--tasks-attach-conversation.md)
- [component · agent.board](interfaces/component--agent-board.md)

## agent.factory · 统一实例工厂

[详细开发设计](../../docs/design/components/agent-factory.md) · 计划位置：`src/uaw/agent/factory.py`。

- [http · agents.get](interfaces/http--agents-get.md)
- [tool · agents.invoke](interfaces/tool--agents-invoke.md)
- [runtime · AgentRuntime.start](interfaces/runtime--AgentRuntime-start.md)
- [component · agent.factory](interfaces/component--agent-factory.md)

## agent.definitions.designer · 角色设计方法

[详细开发设计](../../docs/design/components/agent-definitions-designer.md) · 计划位置：`src/uaw/agent/definitions/designer.py`。

- [tool · agents.create](interfaces/tool--agents-create.md)
- [component · agent.definitions.designer](interfaces/component--agent-definitions-designer.md)

## agent.definitions.validator · 定义与授权校验

[详细开发设计](../../docs/design/components/agent-definitions-validator.md) · 计划位置：`src/uaw/agent/definitions/validator.py`。

- [http · definitions.create](interfaces/http--definitions-create.md)
- [http · definitions.update](interfaces/http--definitions-update.md)
- [tool · agents.create](interfaces/tool--agents-create.md)
- [tool · agents.update](interfaces/tool--agents-update.md)
- [component · agent.definitions.validator](interfaces/component--agent-definitions-validator.md)

## agent.definitions.model_intent · 模型意图解析

[详细开发设计](../../docs/design/components/agent-definitions-model_intent.md) · 计划位置：`src/uaw/agent/definitions/model_intent.py`。

- [http · definitions.create](interfaces/http--definitions-create.md)
- [tool · agents.create](interfaces/tool--agents-create.md)
- [component · agent.definitions.model_intent](interfaces/component--agent-definitions-model-intent.md)

## agent.definitions.repository · 定义提交与版本

[详细开发设计](../../docs/design/components/agent-definitions-repository.md) · 计划位置：`src/uaw/agent/definitions/repository.py`。

- [http · definitions.create](interfaces/http--definitions-create.md)
- [http · definitions.get](interfaces/http--definitions-get.md)
- [http · definitions.update](interfaces/http--definitions-update.md)
- [tool · agents.create](interfaces/tool--agents-create.md)
- [component · agent.definitions.repository](interfaces/component--agent-definitions-repository.md)

## agent.definitions.discovery · 会话Agent发现

[详细开发设计](../../docs/design/components/agent-definitions-discovery.md) · 计划位置：`src/uaw/agent/definitions/discovery.py`。

- [http · definitions.list](interfaces/http--definitions-list.md)
- [tool · tools.discover](interfaces/tool--tools-discover.md)
- [tool · agents.list](interfaces/tool--agents-list.md)
- [component · agent.definitions.discovery](interfaces/component--agent-definitions-discovery.md)

## agent.definitions.change_service · 配置变更与撤销

[详细开发设计](../../docs/design/components/agent-definitions-change_service.md) · 计划位置：`src/uaw/agent/definitions/change_service.py`。

- [http · definitions.update](interfaces/http--definitions-update.md)
- [http · definitions.diff](interfaces/http--definitions-diff.md)
- [http · definitions.revert](interfaces/http--definitions-revert.md)
- [tool · agents.update](interfaces/tool--agents-update.md)
- [component · agent.definitions.change_service](interfaces/component--agent-definitions-change-service.md)

## context.sources · 来源解析

[详细开发设计](../../docs/design/components/context-sources.md) · 计划位置：`src/uaw/context/sources.py`。

- [http · assets.upload.begin](interfaces/http--assets-upload-begin.md)
- [http · references.read](interfaces/http--references-read.md)
- [tool · context.read](interfaces/tool--context-read.md)
- [component · context.sources](interfaces/component--context-sources.md)

## context.rules · 规则与信任装配

[详细开发设计](../../docs/design/components/context-rules.md) · 计划位置：`src/uaw/context/rules.py`。

- [tool · skills.load](interfaces/tool--skills-load.md)
- [component · context.rules](interfaces/component--context-rules.md)

## context.ingestion · 摄取与索引发布

[详细开发设计](../../docs/design/components/context-ingestion.md) · 计划位置：`src/uaw/context/ingestion.py`。

- [http · assets.upload.begin](interfaces/http--assets-upload-begin.md)
- [http · assets.upload.complete](interfaces/http--assets-upload-complete.md)
- [http · sources.ingest](interfaces/http--sources-ingest.md)
- [http · sources.delete](interfaces/http--sources-delete.md)
- [http · sources.get](interfaces/http--sources-get.md)
- [runtime · ContextRuntime.ingest](interfaces/runtime--ContextRuntime-ingest.md)
- [component · context.ingestion](interfaces/component--context-ingestion.md)

## context.retrieval · 资料检索与证据

[详细开发设计](../../docs/design/components/context-retrieval.md) · 计划位置：`src/uaw/context/retrieval.py`。

- [component · context.retrieval](interfaces/component--context-retrieval.md)

## context.memory · 记忆生命周期

[详细开发设计](../../docs/design/components/context-memory.md) · 计划位置：`src/uaw/context/memory/facade.py`。

- [http · memory.list](interfaces/http--memory-list.md)
- [runtime · ContextRuntime.remember](interfaces/runtime--ContextRuntime-remember.md)
- [runtime · ContextRuntime.recall](interfaces/runtime--ContextRuntime-recall.md)
- [component · context.memory](interfaces/component--context-memory.md)

## context.selection · 选择与上下文预算

[详细开发设计](../../docs/design/components/context-selection.md) · 计划位置：`src/uaw/context/selection.py`。

- [component · context.selection](interfaces/component--context-selection.md)

## context.compression · 压缩与关键项保护

[详细开发设计](../../docs/design/components/context-compression.md) · 计划位置：`src/uaw/context/compression.py`。

- [component · context.compression](interfaces/component--context-compression.md)

## context.composer · 装配与快照

[详细开发设计](../../docs/design/components/context-composer.md) · 计划位置：`src/uaw/context/composer.py`。

- [runtime · ContextRuntime.build](interfaces/runtime--ContextRuntime-build.md)
- [component · context.composer](interfaces/component--context-composer.md)

## context.references · 引用登记与解析

[详细开发设计](../../docs/design/components/context-references.md) · 计划位置：`src/uaw/context/references.py`。

- [http · references.resolve](interfaces/http--references-resolve.md)
- [http · references.read](interfaces/http--references-read.md)
- [tool · context.read](interfaces/tool--context-read.md)
- [tool · references.resolve](interfaces/tool--references-resolve.md)
- [tool · references.read](interfaces/tool--references-read.md)
- [tool · web.read](interfaces/tool--web-read.md)
- [runtime · ContextRuntime.resolve_reference](interfaces/runtime--ContextRuntime-resolve-reference.md)
- [component · context.references](interfaces/component--context-references.md)

## tool.registry · 工具注册与版本

[详细开发设计](../../docs/design/components/tool-registry.md) · 计划位置：`src/uaw/tool/registry.py`。

- [http · admin.configuration.validate](interfaces/http--admin-configuration-validate.md)
- [http · admin.tools.register](interfaces/http--admin-tools-register.md)
- [http · admin.tools.list](interfaces/http--admin-tools-list.md)
- [component · tool.registry](interfaces/component--tool-registry.md)

## tool.discovery · 工具发现与筛选

[详细开发设计](../../docs/design/components/tool-discovery.md) · 计划位置：`src/uaw/tool/discovery.py`。

- [tool · tools.discover](interfaces/tool--tools-discover.md)
- [runtime · ToolRuntime.discover](interfaces/runtime--ToolRuntime-discover.md)
- [component · tool.discovery](interfaces/component--tool-discovery.md)

## tool.invocation · 调用闸门与派发

[详细开发设计](../../docs/design/components/tool-invocation.md) · 计划位置：`src/uaw/tool/invocation/facade.py`。

- [runtime · ToolRuntime.invoke](interfaces/runtime--ToolRuntime-invoke.md)
- [component · tool.invocation](interfaces/component--tool-invocation.md)

## tool.effects · 调用与副作用账本

[详细开发设计](../../docs/design/components/tool-effects.md) · 计划位置：`src/uaw/tool/effects.py`。

- [runtime · ToolRuntime.reconcile](interfaces/runtime--ToolRuntime-reconcile.md)
- [component · tool.effects](interfaces/component--tool-effects.md)

## tool.failure · 失败恢复与等价切换

[详细开发设计](../../docs/design/components/tool-failure.md) · 计划位置：`src/uaw/tool/failure.py`。

- [component · tool.failure](interfaces/component--tool-failure.md)

## tool.mcp · MCP 连接与适配

[详细开发设计](../../docs/design/components/tool-mcp.md) · 计划位置：`src/uaw/tool/mcp/facade.py`。

- [component · tool.mcp](interfaces/component--tool-mcp.md)

## tool.adapters · 领域与外部适配器

[详细开发设计](../../docs/design/components/tool-adapters.md) · 计划位置：`src/uaw/tool/adapters.py`。

- [tool · search.query](interfaces/tool--search-query.md)
- [tool · web.read](interfaces/tool--web-read.md)
- [component · tool.adapters](interfaces/component--tool-adapters.md)

## tool.results · 结果规范化与分页

[详细开发设计](../../docs/design/components/tool-results.md) · 计划位置：`src/uaw/tool/results.py`。

- [tool · search.query](interfaces/tool--search-query.md)
- [component · tool.results](interfaces/component--tool-results.md)

## tool.audit · 执行审计与指标

[详细开发设计](../../docs/design/components/tool-audit.md) · 计划位置：`src/uaw/tool/audit.py`。

- [component · tool.audit](interfaces/component--tool-audit.md)

## workspace.binding · 项目绑定与本地授权

[详细开发设计](../../docs/design/components/workspace-binding.md) · 计划位置：`src/uaw/workspace/binding.py`。

- [http · projects.list](interfaces/http--projects-list.md)
- [http · projects.bind](interfaces/http--projects-bind.md)
- [http · projects.get](interfaces/http--projects-get.md)
- [http · projects.unbind](interfaces/http--projects-unbind.md)
- [runner · pair.begin](interfaces/runner--pair-begin.md)
- [runner · pair.complete](interfaces/runner--pair-complete.md)
- [runner · heartbeat](interfaces/runner--heartbeat.md)
- [runner · root.select](interfaces/runner--root-select.md)
- [component · workspace.binding](interfaces/component--workspace-binding.md)

## workspace.base · 输入基础状态

[详细开发设计](../../docs/design/components/workspace-base.md) · 计划位置：`src/uaw/workspace/base.py`。

- [runner · workspace.capture](interfaces/runner--workspace-capture.md)
- [component · workspace.base](interfaces/component--workspace-base.md)

## workspace.isolation · 隔离与分支

[详细开发设计](../../docs/design/components/workspace-isolation.md) · 计划位置：`src/uaw/workspace/isolation.py`。

- [http · workspaces.get](interfaces/http--workspaces-get.md)
- [runtime · WorkspaceRuntime.allocate](interfaces/runtime--WorkspaceRuntime-allocate.md)
- [runner · workspace.allocate](interfaces/runner--workspace-allocate.md)
- [runner · workspace.release](interfaces/runner--workspace-release.md)
- [component · workspace.isolation](interfaces/component--workspace-isolation.md)

## workspace.environment · 环境准备与回收

[详细开发设计](../../docs/design/components/workspace-environment.md) · 计划位置：`src/uaw/workspace/environment.py`。

- [http · admin.environments.register](interfaces/http--admin-environments-register.md)
- [tool · environment.inspect](interfaces/tool--environment-inspect.md)
- [tool · environment.ensure](interfaces/tool--environment-ensure.md)
- [runtime · WorkspaceRuntime.prepare](interfaces/runtime--WorkspaceRuntime-prepare.md)
- [runner · environment.inspect](interfaces/runner--environment-inspect.md)
- [runner · environment.ensure](interfaces/runner--environment-ensure.md)
- [runner · workspace.release](interfaces/runner--workspace-release.md)
- [component · workspace.environment](interfaces/component--workspace-environment.md)

## workspace.process · 文件与进程执行

[详细开发设计](../../docs/design/components/workspace-process.md) · 计划位置：`src/uaw/workspace/process.py`。

- [http · workspaces.files](interfaces/http--workspaces-files.md)
- [http · processes.get](interfaces/http--processes-get.md)
- [http · processes.stop](interfaces/http--processes-stop.md)
- [tool · process.exec](interfaces/tool--process-exec.md)
- [tool · process.poll](interfaces/tool--process-poll.md)
- [tool · process.stop](interfaces/tool--process-stop.md)
- [tool · file.read](interfaces/tool--file-read.md)
- [tool · file.write](interfaces/tool--file-write.md)
- [tool · verification.run](interfaces/tool--verification-run.md)
- [runner · file.read](interfaces/runner--file-read.md)
- [runner · file.write](interfaces/runner--file-write.md)
- [runner · file.list](interfaces/runner--file-list.md)
- [runner · process.exec](interfaces/runner--process-exec.md)
- [runner · process.poll](interfaces/runner--process-poll.md)
- [runner · process.stop](interfaces/runner--process-stop.md)
- [component · workspace.process](interfaces/component--workspace-process.md)

## workspace.changes · 变更与冲突合并

[详细开发设计](../../docs/design/components/workspace-changes.md) · 计划位置：`src/uaw/workspace/changes.py`。

- [http · workspaces.changes](interfaces/http--workspaces-changes.md)
- [http · workspaces.merge](interfaces/http--workspaces-merge.md)
- [http · workspaces.revert](interfaces/http--workspaces-revert.md)
- [tool · workspace.changes](interfaces/tool--workspace-changes.md)
- [tool · workspace.revert](interfaces/tool--workspace-revert.md)
- [tool · file.write](interfaces/tool--file-write.md)
- [runtime · WorkspaceRuntime.merge](interfaces/runtime--WorkspaceRuntime-merge.md)
- [runtime · WorkspaceRuntime.revert](interfaces/runtime--WorkspaceRuntime-revert.md)
- [runner · file.write](interfaces/runner--file-write.md)
- [runner · changes.capture](interfaces/runner--changes-capture.md)
- [runner · changes.merge](interfaces/runner--changes-merge.md)
- [runner · changes.revert](interfaces/runner--changes-revert.md)
- [component · workspace.changes](interfaces/component--workspace-changes.md)

## workspace.artifacts · 产物与格式适配

[详细开发设计](../../docs/design/components/workspace-artifacts.md) · 计划位置：`src/uaw/workspace/artifacts.py`。

- [http · artifacts.list](interfaces/http--artifacts-list.md)
- [http · artifacts.get](interfaces/http--artifacts-get.md)
- [http · artifacts.preview](interfaces/http--artifacts-preview.md)
- [http · artifacts.export](interfaces/http--artifacts-export.md)
- [tool · artifacts.publish](interfaces/tool--artifacts-publish.md)
- [component · workspace.artifacts](interfaces/component--workspace-artifacts.md)

## workspace.review · 审阅与局部接受

[详细开发设计](../../docs/design/components/workspace-review.md) · 计划位置：`src/uaw/workspace/review.py`。

- [http · reviews.get](interfaces/http--reviews-get.md)
- [http · reviews.decide](interfaces/http--reviews-decide.md)
- [runtime · WorkspaceRuntime.review](interfaces/runtime--WorkspaceRuntime-review.md)
- [component · workspace.review](interfaces/component--workspace-review.md)

## model.catalog · 可见模型目录

[详细开发设计](../../docs/design/components/model-catalog.md) · 计划位置：`src/uaw/model/catalog.py`。

- [http · models.list](interfaces/http--models-list.md)
- [http · admin.configuration.validate](interfaces/http--admin-configuration-validate.md)
- [http · admin.models.register](interfaces/http--admin-models-register.md)
- [tool · models.list](interfaces/tool--models-list.md)
- [runtime · ModelRuntime.list](interfaces/runtime--ModelRuntime-list.md)
- [component · model.catalog](interfaces/component--model-catalog.md)

## model.policy · 选择与模型继承

[详细开发设计](../../docs/design/components/model-policy.md) · 计划位置：`src/uaw/model/policy.py`。

- [http · conversations.create](interfaces/http--conversations-create.md)
- [http · conversations.configure](interfaces/http--conversations-configure.md)
- [runtime · ModelRuntime.resolve_policy](interfaces/runtime--ModelRuntime-resolve-policy.md)
- [component · model.policy](interfaces/component--model-policy.md)

## model.capability · 兼容与Auto选择

[详细开发设计](../../docs/design/components/model-capability.md) · 计划位置：`src/uaw/model/capability.py`。

- [component · model.capability](interfaces/component--model-capability.md)

## model.gateway · 调用网关

[详细开发设计](../../docs/design/components/model-gateway.md) · 计划位置：`src/uaw/model/gateway.py`。

- [runtime · ModelRuntime.generate](interfaces/runtime--ModelRuntime-generate.md)
- [component · model.gateway](interfaces/component--model-gateway.md)

## model.adapters · 供应商协议适配

[详细开发设计](../../docs/design/components/model-adapters.md) · 计划位置：`src/uaw/model/adapters.py`。

- [http · admin.providers.configure](interfaces/http--admin-providers-configure.md)
- [component · model.adapters](interfaces/component--model-adapters.md)

## model.recovery · 调用恢复

[详细开发设计](../../docs/design/components/model-recovery.md) · 计划位置：`src/uaw/model/recovery.py`。

- [component · model.recovery](interfaces/component--model-recovery.md)

## model.usage · 计量与版本记录

[详细开发设计](../../docs/design/components/model-usage.md) · 计划位置：`src/uaw/model/usage.py`。

- [component · model.usage](interfaces/component--model-usage.md)

## run.history · 历史与输入权威

[详细开发设计](../../docs/design/components/run-history.md) · 计划位置：`src/uaw/run/history.py`。

- [http · conversations.create](interfaces/http--conversations-create.md)
- [http · conversations.list](interfaces/http--conversations-list.md)
- [http · conversations.get](interfaces/http--conversations-get.md)
- [http · conversations.configure](interfaces/http--conversations-configure.md)
- [http · conversations.items](interfaces/http--conversations-items.md)
- [http · turns.submit](interfaces/http--turns-submit.md)
- [http · tasks.get](interfaces/http--tasks-get.md)
- [runtime · RunRuntime.create](interfaces/runtime--RunRuntime-create.md)
- [http · tasks.attach_conversation](interfaces/http--tasks-attach-conversation.md)
- [component · run.history](interfaces/component--run-history.md)

## run.state · Run 与交互项

[详细开发设计](../../docs/design/components/run-state.md) · 计划位置：`src/uaw/run/state.py`。

- [http · turns.submit](interfaces/http--turns-submit.md)
- [http · runs.get](interfaces/http--runs-get.md)
- [runtime · RunRuntime.create](interfaces/runtime--RunRuntime-create.md)
- [http · tasks.attach_conversation](interfaces/http--tasks-attach-conversation.md)
- [component · run.state](interfaces/component--run-state.md)

## run.events · 事件与重连

[详细开发设计](../../docs/design/components/run-events.md) · 计划位置：`src/uaw/run/events.py`。

- [http · conversations.items](interfaces/http--conversations-items.md)
- [http · events.read](interfaces/http--events-read.md)
- [http · events.stream](interfaces/http--events-stream.md)
- [http · events.payload](interfaces/http--events-payload.md)
- [component · run.events](interfaces/component--run-events.md)

## run.budget · 预算与准入

[详细开发设计](../../docs/design/components/run-budget.md) · 计划位置：`src/uaw/run/budget.py`。

- [component · run.budget](interfaces/component--run-budget.md)

## run.approval · 审批与用户控制

[详细开发设计](../../docs/design/components/run-approval.md) · 计划位置：`src/uaw/run/approval.py`。

- [http · runs.control](interfaces/http--runs-control.md)
- [http · approvals.get](interfaces/http--approvals-get.md)
- [http · approvals.decide](interfaces/http--approvals-decide.md)
- [http · admin.policies.register](interfaces/http--admin-policies-register.md)
- [tool · interaction.ask_user](interfaces/tool--interaction-ask-user.md)
- [runtime · RunRuntime.control](interfaces/runtime--RunRuntime-control.md)
- [component · run.approval](interfaces/component--run-approval.md)

## run.checkpoint · 恢复边界与版本

[详细开发设计](../../docs/design/components/run-checkpoint.md) · 计划位置：`src/uaw/run/checkpoint.py`。

- [http · runs.checkpoint](interfaces/http--runs-checkpoint.md)
- [runtime · RunRuntime.checkpoint](interfaces/runtime--RunRuntime-checkpoint.md)
- [component · run.checkpoint](interfaces/component--run-checkpoint.md)

## run.resume · 租约与执行恢复

[详细开发设计](../../docs/design/components/run-resume.md) · 计划位置：`src/uaw/run/resume/facade.py`。

- [http · runs.resume](interfaces/http--runs-resume.md)
- [runtime · RunRuntime.resume](interfaces/runtime--RunRuntime-resume.md)
- [component · run.resume](interfaces/component--run-resume.md)

## run.cancel · 取消传播

[详细开发设计](../../docs/design/components/run-cancel.md) · 计划位置：`src/uaw/run/cancel.py`。

- [http · runs.control](interfaces/http--runs-control.md)
- [http · agents.cancel](interfaces/http--agents-cancel.md)
- [http · projects.unbind](interfaces/http--projects-unbind.md)
- [http · processes.stop](interfaces/http--processes-stop.md)
- [tool · agents.cancel](interfaces/tool--agents-cancel.md)
- [runtime · RunRuntime.control](interfaces/runtime--RunRuntime-control.md)
- [component · run.cancel](interfaces/component--run-cancel.md)

## run.trigger · 未来触发器

[详细开发设计](../../docs/design/components/run-trigger.md) · 计划位置：`src/uaw/run/trigger.py`。

- [http · triggers.create](interfaces/http--triggers-create.md)
- [http · triggers.disable](interfaces/http--triggers-disable.md)
- [component · run.trigger](interfaces/component--run-trigger.md)

## support.configuration · 配置与账号控制层

[详细开发设计](../../docs/design/components/support-configuration.md) · 计划位置：`src/uaw/shared/configuration.py`。

- [http · connections.list](interfaces/http--connections-list.md)
- [http · connections.begin](interfaces/http--connections-begin.md)
- [http · connections.revoke](interfaces/http--connections-revoke.md)
- [http · admin.configuration.get](interfaces/http--admin-configuration-get.md)
- [http · admin.configuration.stage](interfaces/http--admin-configuration-stage.md)
- [http · admin.configuration.validate](interfaces/http--admin-configuration-validate.md)
- [http · admin.configuration.activate](interfaces/http--admin-configuration-activate.md)
- [http · admin.providers.configure](interfaces/http--admin-providers-configure.md)
- [http · admin.secrets.put](interfaces/http--admin-secrets-put.md)
- [http · admin.policies.register](interfaces/http--admin-policies-register.md)
- [http · admin.providers.revoke](interfaces/http--admin-providers-revoke.md)
- [component · support.configuration](interfaces/component--support-configuration.md)

## support.extensions · 扩展包与版本发布

[详细开发设计](../../docs/design/components/support-extensions.md) · 计划位置：`src/uaw/shared/extensions.py`。

- [http · skills.list](interfaces/http--skills-list.md)
- [http · admin.extensions.install](interfaces/http--admin-extensions-install.md)
- [http · admin.extensions.activate](interfaces/http--admin-extensions-activate.md)
- [http · admin.extensions.revoke](interfaces/http--admin-extensions-revoke.md)
- [http · admin.extensions.validate](interfaces/http--admin-extensions-validate.md)
- [http · admin.extensions.rollback](interfaces/http--admin-extensions-rollback.md)
- [component · support.extensions](interfaces/component--support-extensions.md)

## support.cache · 共享缓存设施

[详细开发设计](../../docs/design/components/support-cache.md) · 计划位置：`src/uaw/shared/cache.py`。

- [http · sources.delete](interfaces/http--sources-delete.md)
- [http · memory.forget](interfaces/http--memory-forget.md)
- [http · admin.policies.register](interfaces/http--admin-policies-register.md)
- [component · support.cache](interfaces/component--support-cache.md)

## support.observability · 运行观测

[详细开发设计](../../docs/design/components/support-observability.md) · 计划位置：`src/uaw/shared/observability.py`。

- [http · admin.traces.list](interfaces/http--admin-traces-list.md)
- [component · support.observability](interfaces/component--support-observability.md)

## support.evaluation · 离线质量评测

[详细开发设计](../../docs/design/components/support-evaluation.md) · 计划位置：`src/uaw/shared/evaluation.py`。

- [http · admin.evaluations.run](interfaces/http--admin-evaluations-run.md)
- [http · admin.evaluations.get](interfaces/http--admin-evaluations-get.md)
- [component · support.evaluation](interfaces/component--support-evaluation.md)

## support.stores · 存储适配与访问

[详细开发设计](../../docs/design/components/support-stores.md) · 计划位置：`src/uaw/shared/stores.py`。

- [component · support.stores](interfaces/component--support-stores.md)

## tool.invocation.schema · 参数与可信上下文

[详细开发设计](../../docs/design/components/tool-invocation-schema.md) · 计划位置：`src/uaw/tool/invocation/schema.py`。

- [component · tool.invocation.schema](interfaces/component--tool-invocation-schema.md)

## tool.invocation.precheck · 执行预检

[详细开发设计](../../docs/design/components/tool-invocation-precheck.md) · 计划位置：`src/uaw/tool/invocation/precheck.py`。

- [component · tool.invocation.precheck](interfaces/component--tool-invocation-precheck.md)

## tool.invocation.approval · 必要审批等待

[详细开发设计](../../docs/design/components/tool-invocation-approval.md) · 计划位置：`src/uaw/tool/invocation/approval.py`。

- [http · approvals.decide](interfaces/http--approvals-decide.md)
- [component · tool.invocation.approval](interfaces/component--tool-invocation-approval.md)

## tool.invocation.recheck · 执行前复核

[详细开发设计](../../docs/design/components/tool-invocation-recheck.md) · 计划位置：`src/uaw/tool/invocation/recheck.py`。

- [http · approvals.decide](interfaces/http--approvals-decide.md)
- [component · tool.invocation.recheck](interfaces/component--tool-invocation-recheck.md)

## tool.invocation.dispatch · 意图登记与执行

[详细开发设计](../../docs/design/components/tool-invocation-dispatch.md) · 计划位置：`src/uaw/tool/invocation/dispatch.py`。

- [component · tool.invocation.dispatch](interfaces/component--tool-invocation-dispatch.md)

## tool.invocation.result · 规范结果与结算

[详细开发设计](../../docs/design/components/tool-invocation-result.md) · 计划位置：`src/uaw/tool/invocation/result.py`。

- [component · tool.invocation.result](interfaces/component--tool-invocation-result.md)

## agent.collaboration.contract · 子任务契约

[详细开发设计](../../docs/design/components/agent-collaboration-contract.md) · 计划位置：`src/uaw/agent/collaboration/contract.py`。

- [tool · agents.invoke](interfaces/tool--agents-invoke.md)
- [component · agent.collaboration.contract](interfaces/component--agent-collaboration-contract.md)

## agent.collaboration.instance · 隔离运行实例

[详细开发设计](../../docs/design/components/agent-collaboration-instance.md) · 计划位置：`src/uaw/agent/collaboration/instance.py`。

- [tool · agents.invoke](interfaces/tool--agents-invoke.md)
- [component · agent.collaboration.instance](interfaces/component--agent-collaboration-instance.md)

## agent.collaboration.channel · 消息与受控引用

[详细开发设计](../../docs/design/components/agent-collaboration-channel.md) · 计划位置：`src/uaw/agent/collaboration/channel.py`。

- [tool · agents.wait](interfaces/tool--agents-wait.md)
- [tool · agents.message](interfaces/tool--agents-message.md)
- [component · agent.collaboration.channel](interfaces/component--agent-collaboration-channel.md)

## agent.collaboration.join · 结果核验与汇总

[详细开发设计](../../docs/design/components/agent-collaboration-join.md) · 计划位置：`src/uaw/agent/collaboration/join.py`。

- [tool · agents.wait](interfaces/tool--agents-wait.md)
- [component · agent.collaboration.join](interfaces/component--agent-collaboration-join.md)

## agent.collaboration.handoff · 可选控制权交接

[详细开发设计](../../docs/design/components/agent-collaboration-handoff.md) · 计划位置：`src/uaw/agent/collaboration/handoff.py`。

- [tool · agents.handoff](interfaces/tool--agents-handoff.md)
- [component · agent.collaboration.handoff](interfaces/component--agent-collaboration-handoff.md)

## agent.collaboration.cancel · 生命周期与取消

[详细开发设计](../../docs/design/components/agent-collaboration-cancel.md) · 计划位置：`src/uaw/agent/collaboration/cancel.py`。

- [http · agents.cancel](interfaces/http--agents-cancel.md)
- [tool · agents.cancel](interfaces/tool--agents-cancel.md)
- [component · agent.collaboration.cancel](interfaces/component--agent-collaboration-cancel.md)

## agent.completion.contract · 语义交付契约

[详细开发设计](../../docs/design/components/agent-completion-contract.md) · 计划位置：`src/uaw/agent/completion/contract.py`。

- [tool · tasks.verify](interfaces/tool--tasks-verify.md)
- [component · agent.completion.contract](interfaces/component--agent-completion-contract.md)

## agent.completion.evidence · 真实证据收集

[详细开发设计](../../docs/design/components/agent-completion-evidence.md) · 计划位置：`src/uaw/agent/completion/evidence.py`。

- [tool · tasks.verify](interfaces/tool--tasks-verify.md)
- [tool · verification.run](interfaces/tool--verification-run.md)
- [component · agent.completion.evidence](interfaces/component--agent-completion-evidence.md)

## agent.completion.semantic · 语义核对

[详细开发设计](../../docs/design/components/agent-completion-semantic.md) · 计划位置：`src/uaw/agent/completion/semantic.py`。

- [http · verification.get](interfaces/http--verification-get.md)
- [tool · tasks.verify](interfaces/tool--tasks-verify.md)
- [tool · verification.report](interfaces/tool--verification-report.md)
- [component · agent.completion.semantic](interfaces/component--agent-completion-semantic.md)

## agent.completion.version · 版本与硬条件校验

[详细开发设计](../../docs/design/components/agent-completion-version.md) · 计划位置：`src/uaw/agent/completion/version.py`。

- [tool · tasks.verify](interfaces/tool--tasks-verify.md)
- [component · agent.completion.version](interfaces/component--agent-completion-version.md)

## agent.completion.delivery · 提交交付

[详细开发设计](../../docs/design/components/agent-completion-delivery.md) · 计划位置：`src/uaw/agent/completion/delivery.py`。

- [component · agent.completion.delivery](interfaces/component--agent-completion-delivery.md)

## agent.completion.acceptance · 用户接受与迭代

[详细开发设计](../../docs/design/components/agent-completion-acceptance.md) · 计划位置：`src/uaw/agent/completion/acceptance.py`。

- [http · reviews.decide](interfaces/http--reviews-decide.md)
- [component · agent.completion.acceptance](interfaces/component--agent-completion-acceptance.md)

## context.memory.candidate · 记忆候选

[详细开发设计](../../docs/design/components/context-memory-candidate.md) · 计划位置：`src/uaw/context/memory/candidate.py`。

- [tool · memory.remember](interfaces/tool--memory-remember.md)
- [component · context.memory.candidate](interfaces/component--context-memory-candidate.md)

## context.memory.policy · 范围与写入政策

[详细开发设计](../../docs/design/components/context-memory-policy.md) · 计划位置：`src/uaw/context/memory/policy.py`。

- [http · conversations.configure](interfaces/http--conversations-configure.md)
- [tool · memory.remember](interfaces/tool--memory-remember.md)
- [component · context.memory.policy](interfaces/component--context-memory-policy.md)

## context.memory.conflict · 查重与冲突

[详细开发设计](../../docs/design/components/context-memory-conflict.md) · 计划位置：`src/uaw/context/memory/conflict.py`。

- [tool · memory.remember](interfaces/tool--memory-remember.md)
- [component · context.memory.conflict](interfaces/component--context-memory-conflict.md)

## context.memory.store · 提交与召回

[详细开发设计](../../docs/design/components/context-memory-store.md) · 计划位置：`src/uaw/context/memory/store.py`。

- [http · memory.list](interfaces/http--memory-list.md)
- [tool · memory.remember](interfaces/tool--memory-remember.md)
- [tool · memory.recall](interfaces/tool--memory-recall.md)
- [component · context.memory.store](interfaces/component--context-memory-store.md)

## context.memory.forget · 遗忘与删除传播

[详细开发设计](../../docs/design/components/context-memory-forget.md) · 计划位置：`src/uaw/context/memory/forget.py`。

- [http · memory.forget](interfaces/http--memory-forget.md)
- [tool · memory.forget](interfaces/tool--memory-forget.md)
- [runtime · ContextRuntime.forget](interfaces/runtime--ContextRuntime-forget.md)
- [component · context.memory.forget](interfaces/component--context-memory-forget.md)

## tool.mcp.provider · 提供方绑定

[详细开发设计](../../docs/design/components/tool-mcp-provider.md) · 计划位置：`src/uaw/tool/mcp/provider.py`。

- [http · connections.begin](interfaces/http--connections-begin.md)
- [http · admin.providers.configure](interfaces/http--admin-providers-configure.md)
- [component · tool.mcp.provider](interfaces/component--tool-mcp-provider.md)

## tool.mcp.session · 协议会话

[详细开发设计](../../docs/design/components/tool-mcp-session.md) · 计划位置：`src/uaw/tool/mcp/session.py`。

- [component · tool.mcp.session](interfaces/component--tool-mcp-session.md)

## tool.mcp.capabilities · 能力规范化

[详细开发设计](../../docs/design/components/tool-mcp-capabilities.md) · 计划位置：`src/uaw/tool/mcp/capabilities.py`。

- [component · tool.mcp.capabilities](interfaces/component--tool-mcp-capabilities.md)

## tool.mcp.invoke · 闸门后调用

[详细开发设计](../../docs/design/components/tool-mcp-invoke.md) · 计划位置：`src/uaw/tool/mcp/invoke.py`。

- [component · tool.mcp.invoke](interfaces/component--tool-mcp-invoke.md)

## tool.mcp.invalidate · 变化与撤销

[详细开发设计](../../docs/design/components/tool-mcp-invalidate.md) · 计划位置：`src/uaw/tool/mcp/invalidate.py`。

- [http · connections.revoke](interfaces/http--connections-revoke.md)
- [http · admin.extensions.revoke](interfaces/http--admin-extensions-revoke.md)
- [component · tool.mcp.invalidate](interfaces/component--tool-mcp-invalidate.md)

## run.resume.lease · 取得运行租约

[详细开发设计](../../docs/design/components/run-resume-lease.md) · 计划位置：`src/uaw/run/resume/lease.py`。

- [http · runs.resume](interfaces/http--runs-resume.md)
- [component · run.resume.lease](interfaces/component--run-resume-lease.md)

## run.resume.versions · 版本兼容检查

[详细开发设计](../../docs/design/components/run-resume-versions.md) · 计划位置：`src/uaw/run/resume/versions.py`。

- [http · runs.resume](interfaces/http--runs-resume.md)
- [component · run.resume.versions](interfaces/component--run-resume-versions.md)

## run.resume.access · 重建连接与核验

[详细开发设计](../../docs/design/components/run-resume-access.md) · 计划位置：`src/uaw/run/resume/access.py`。

- [http · runs.resume](interfaces/http--runs-resume.md)
- [component · run.resume.access](interfaces/component--run-resume-access.md)

## run.resume.effects · Tool未决动作对账

[详细开发设计](../../docs/design/components/run-resume-effects.md) · 计划位置：`src/uaw/run/resume/effects.py`。

- [http · runs.resume](interfaces/http--runs-resume.md)
- [component · run.resume.effects](interfaces/component--run-resume-effects.md)

## run.resume.workspace · 工作区实际版本

[详细开发设计](../../docs/design/components/run-resume-workspace.md) · 计划位置：`src/uaw/run/resume/workspace.py`。

- [http · runs.resume](interfaces/http--runs-resume.md)
- [component · run.resume.workspace](interfaces/component--run-resume-workspace.md)

## run.resume.continue · 恢复可运行工作

[详细开发设计](../../docs/design/components/run-resume-continue.md) · 计划位置：`src/uaw/run/resume/continue_run.py`。

- [http · runs.resume](interfaces/http--runs-resume.md)
- [component · run.resume.continue](interfaces/component--run-resume-continue.md)

