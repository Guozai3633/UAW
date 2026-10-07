# 模型可调用工具

[接口总入口](README.md)。状态：设计契约0.1。

| 接口 | 输入 | 成功payload | 效果 |
| --- | --- | --- | --- |
| [tools.discover](interfaces/tool--tools-discover.md) | [ToolToolsDiscoverInput](objects/ToolToolsDiscoverInput.md) | [DiscoveryResult](objects/DiscoveryResult.md) | `read` |
| [context.read](interfaces/tool--context-read.md) | [ToolContextReadInput](objects/ToolContextReadInput.md) | [ReadResult](objects/ReadResult.md) | `read` |
| [skills.load](interfaces/tool--skills-load.md) | [ToolSkillsLoadInput](objects/ToolSkillsLoadInput.md) | [SkillSpec](objects/SkillSpec.md) | `read` |
| [agents.create](interfaces/tool--agents-create.md) | [ToolAgentsCreateInput](objects/ToolAgentsCreateInput.md) | [DefinitionBatchResult](objects/DefinitionBatchResult.md) | `internal_write` |
| [agents.update](interfaces/tool--agents-update.md) | [ToolAgentsUpdateInput](objects/ToolAgentsUpdateInput.md) | [AgentDefinitionVersion](objects/AgentDefinitionVersion.md) | `internal_write` |
| [agents.list](interfaces/tool--agents-list.md) | [ToolAgentsListInput](objects/ToolAgentsListInput.md) | [CandidatePage](objects/CandidatePage.md) | `read` |
| [agents.invoke](interfaces/tool--agents-invoke.md) | [ToolAgentsInvokeInput](objects/ToolAgentsInvokeInput.md) | [AgentInstance](objects/AgentInstance.md) | `internal_write` |
| [agents.wait](interfaces/tool--agents-wait.md) | [ToolAgentsWaitInput](objects/ToolAgentsWaitInput.md) | [AgentWaitResult](objects/AgentWaitResult.md) | `read` |
| [agents.message](interfaces/tool--agents-message.md) | [ToolAgentsMessageInput](objects/ToolAgentsMessageInput.md) | [AgentMessage](objects/AgentMessage.md) | `internal_write` |
| [agents.cancel](interfaces/tool--agents-cancel.md) | [ToolAgentsCancelInput](objects/ToolAgentsCancelInput.md) | [CancellationResult](objects/CancellationResult.md) | `internal_write` |
| [agents.handoff](interfaces/tool--agents-handoff.md) | [ToolAgentsHandoffInput](objects/ToolAgentsHandoffInput.md) | [ControlLease](objects/ControlLease.md) | `internal_write` |
| [tasks.assess](interfaces/tool--tasks-assess.md) | [ToolTasksAssessInput](objects/ToolTasksAssessInput.md) | [ExecutionAssessment](objects/ExecutionAssessment.md) | `read` |
| [tasks.plan](interfaces/tool--tasks-plan.md) | [ToolTasksPlanInput](objects/ToolTasksPlanInput.md) | [TaskGraph](objects/TaskGraph.md) | `internal_write` |
| [tasks.verify](interfaces/tool--tasks-verify.md) | [ToolTasksVerifyInput](objects/ToolTasksVerifyInput.md) | [VerificationReport](objects/VerificationReport.md) | `read` |
| [models.list](interfaces/tool--models-list.md) | [ToolModelsListInput](objects/ToolModelsListInput.md) | [ModelPage](objects/ModelPage.md) | `read` |
| [workspace.changes](interfaces/tool--workspace-changes.md) | [ToolWorkspaceChangesInput](objects/ToolWorkspaceChangesInput.md) | [ChangeSet](objects/ChangeSet.md) | `read` |
| [workspace.revert](interfaces/tool--workspace-revert.md) | [ToolWorkspaceRevertInput](objects/ToolWorkspaceRevertInput.md) | [MergeResult](objects/MergeResult.md) | `workspace_write` |
| [references.resolve](interfaces/tool--references-resolve.md) | [ToolReferencesResolveInput](objects/ToolReferencesResolveInput.md) | [ResolvedReference](objects/ResolvedReference.md) | `read` |
| [references.read](interfaces/tool--references-read.md) | [ToolReferencesReadInput](objects/ToolReferencesReadInput.md) | [ReadResult](objects/ReadResult.md) | `read` |
| [environment.inspect](interfaces/tool--environment-inspect.md) | [ToolEnvironmentInspectInput](objects/ToolEnvironmentInspectInput.md) | [EnvironmentRecord](objects/EnvironmentRecord.md) | `read` |
| [environment.ensure](interfaces/tool--environment-ensure.md) | [ToolEnvironmentEnsureInput](objects/ToolEnvironmentEnsureInput.md) | [EnvironmentRecord](objects/EnvironmentRecord.md) | `process` |
| [process.exec](interfaces/tool--process-exec.md) | [ToolProcessExecInput](objects/ToolProcessExecInput.md) | [ProcessRecord](objects/ProcessRecord.md) | `process` |
| [process.poll](interfaces/tool--process-poll.md) | [ToolProcessPollInput](objects/ToolProcessPollInput.md) | [ProcessRecord](objects/ProcessRecord.md) | `read` |
| [process.stop](interfaces/tool--process-stop.md) | [ToolProcessStopInput](objects/ToolProcessStopInput.md) | [ProcessRecord](objects/ProcessRecord.md) | `process` |
| [file.read](interfaces/tool--file-read.md) | [ToolFileReadInput](objects/ToolFileReadInput.md) | [FileContent](objects/FileContent.md) | `read` |
| [file.write](interfaces/tool--file-write.md) | [ToolFileWriteInput](objects/ToolFileWriteInput.md) | [ChangeSet](objects/ChangeSet.md) | `workspace_write` |
| [search.query](interfaces/tool--search-query.md) | [ToolSearchQueryInput](objects/ToolSearchQueryInput.md) | [SearchPage](objects/SearchPage.md) | `read` |
| [web.read](interfaces/tool--web-read.md) | [ToolWebReadInput](objects/ToolWebReadInput.md) | [ReadResult](objects/ReadResult.md) | `read` |
| [verification.run](interfaces/tool--verification-run.md) | [ToolVerificationRunInput](objects/ToolVerificationRunInput.md) | [VerificationCheck](objects/VerificationCheck.md) | `process` |
| [verification.report](interfaces/tool--verification-report.md) | [ToolVerificationReportInput](objects/ToolVerificationReportInput.md) | [VerificationReport](objects/VerificationReport.md) | `read` |
| [artifacts.publish](interfaces/tool--artifacts-publish.md) | [ToolArtifactsPublishInput](objects/ToolArtifactsPublishInput.md) | [ArtifactRecord](objects/ArtifactRecord.md) | `internal_write` |
| [interaction.ask_user](interfaces/tool--interaction-ask-user.md) | [ToolInteractionAsk_userInput](objects/ToolInteractionAsk_userInput.md) | [InteractionItem](objects/InteractionItem.md) | `internal_write` |
| [memory.remember](interfaces/tool--memory-remember.md) | [ToolMemoryRememberInput](objects/ToolMemoryRememberInput.md) | [MemoryRecord](objects/MemoryRecord.md) | `internal_write` |
| [memory.recall](interfaces/tool--memory-recall.md) | [ToolMemoryRecallInput](objects/ToolMemoryRecallInput.md) | [MemoryPage](objects/MemoryPage.md) | `read` |
| [memory.forget](interfaces/tool--memory-forget.md) | [ToolMemoryForgetInput](objects/ToolMemoryForgetInput.md) | [DeletionReceipt](objects/DeletionReceipt.md) | `internal_write` |
