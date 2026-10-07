# Runtime 公共入口

[接口总入口](README.md)。状态：设计契约0.1。

| 接口 | 输入 | 成功payload | 效果 |
| --- | --- | --- | --- |
| [IntentRuntime.preview](interfaces/runtime--IntentRuntime-preview.md) | [IntentPreviewRequest](objects/IntentPreviewRequest.md) | [DraftPreview](objects/DraftPreview.md) | `read` |
| [IntentRuntime.understand](interfaces/runtime--IntentRuntime-understand.md) | [UnderstandingRequest](objects/UnderstandingRequest.md) | [TaskFrame](objects/TaskFrame.md) | `internal_write` |
| [IntentRuntime.revise](interfaces/runtime--IntentRuntime-revise.md) | [FramePatchRequest](objects/FramePatchRequest.md) | [TaskFrame](objects/TaskFrame.md) | `internal_write` |
| [AgentRuntime.define_agent](interfaces/runtime--AgentRuntime-define-agent.md) | [ToolAgentsCreateInput](objects/ToolAgentsCreateInput.md) | [DefinitionBatchResult](objects/DefinitionBatchResult.md) | `internal_write` |
| [AgentRuntime.start](interfaces/runtime--AgentRuntime-start.md) | [AgentStartRequest](objects/AgentStartRequest.md) | [AgentInstance](objects/AgentInstance.md) | `internal_write` |
| [AgentRuntime.step](interfaces/runtime--AgentRuntime-step.md) | [AgentStepRequest](objects/AgentStepRequest.md) | [AgentStepResult](objects/AgentStepResult.md) | `internal_write` |
| [AgentRuntime.delegate](interfaces/runtime--AgentRuntime-delegate.md) | [DelegationSpec](objects/DelegationSpec.md) | [AgentInstance](objects/AgentInstance.md) | `internal_write` |
| [AgentRuntime.verify](interfaces/runtime--AgentRuntime-verify.md) | [ToolTasksVerifyInput](objects/ToolTasksVerifyInput.md) | [VerificationReport](objects/VerificationReport.md) | `read` |
| [ContextRuntime.build](interfaces/runtime--ContextRuntime-build.md) | [ContextRequest](objects/ContextRequest.md) | [ContextSnapshot](objects/ContextSnapshot.md) | `read` |
| [ContextRuntime.ingest](interfaces/runtime--ContextRuntime-ingest.md) | [SourcesIngestRequest](objects/SourcesIngestRequest.md) | [IngestionRecord](objects/IngestionRecord.md) | `internal_write` |
| [ContextRuntime.remember](interfaces/runtime--ContextRuntime-remember.md) | [MemoryCandidate](objects/MemoryCandidate.md) | [MemoryRecord](objects/MemoryRecord.md) | `internal_write` |
| [ContextRuntime.recall](interfaces/runtime--ContextRuntime-recall.md) | [ToolMemoryRecallInput](objects/ToolMemoryRecallInput.md) | [MemoryPage](objects/MemoryPage.md) | `read` |
| [ContextRuntime.forget](interfaces/runtime--ContextRuntime-forget.md) | [MemorySelector](objects/MemorySelector.md) | [DeletionReceipt](objects/DeletionReceipt.md) | `internal_write` |
| [ContextRuntime.resolve_reference](interfaces/runtime--ContextRuntime-resolve-reference.md) | [RefRequest](objects/RefRequest.md) | [ResolvedReference](objects/ResolvedReference.md) | `read` |
| [ToolRuntime.discover](interfaces/runtime--ToolRuntime-discover.md) | [ToolToolsDiscoverInput](objects/ToolToolsDiscoverInput.md) | [DiscoveryResult](objects/DiscoveryResult.md) | `read` |
| [ToolRuntime.invoke](interfaces/runtime--ToolRuntime-invoke.md) | [ToolCall](objects/ToolCall.md) | [ToolResult](objects/ToolResult.md) | `external_write` |
| [ToolRuntime.reconcile](interfaces/runtime--ToolRuntime-reconcile.md) | [ReconcileRequest](objects/ReconcileRequest.md) | [EffectRecord](objects/EffectRecord.md) | `read` |
| [WorkspaceRuntime.allocate](interfaces/runtime--WorkspaceRuntime-allocate.md) | [WorkspaceSpec](objects/WorkspaceSpec.md) | [WorkspaceRecord](objects/WorkspaceRecord.md) | `internal_write` |
| [WorkspaceRuntime.prepare](interfaces/runtime--WorkspaceRuntime-prepare.md) | [ToolEnvironmentEnsureInput](objects/ToolEnvironmentEnsureInput.md) | [EnvironmentRecord](objects/EnvironmentRecord.md) | `process` |
| [WorkspaceRuntime.merge](interfaces/runtime--WorkspaceRuntime-merge.md) | [WorkspacesMergeRequest](objects/WorkspacesMergeRequest.md) | [MergeResult](objects/MergeResult.md) | `workspace_write` |
| [WorkspaceRuntime.revert](interfaces/runtime--WorkspaceRuntime-revert.md) | [WorkspacesRevertRequest](objects/WorkspacesRevertRequest.md) | [MergeResult](objects/MergeResult.md) | `workspace_write` |
| [WorkspaceRuntime.review](interfaces/runtime--WorkspaceRuntime-review.md) | [ReviewsDecideRequest](objects/ReviewsDecideRequest.md) | [ReviewSet](objects/ReviewSet.md) | `internal_write` |
| [ModelRuntime.resolve_policy](interfaces/runtime--ModelRuntime-resolve-policy.md) | [ModelPolicyRequest](objects/ModelPolicyRequest.md) | [ResolvedModelPolicy](objects/ResolvedModelPolicy.md) | `read` |
| [ModelRuntime.list](interfaces/runtime--ModelRuntime-list.md) | [ToolModelsListInput](objects/ToolModelsListInput.md) | [ModelPage](objects/ModelPage.md) | `read` |
| [ModelRuntime.generate](interfaces/runtime--ModelRuntime-generate.md) | [ModelCall](objects/ModelCall.md) | [ModelOutput](objects/ModelOutput.md) | `read` |
| [RunRuntime.create](interfaces/runtime--RunRuntime-create.md) | [RunCreateRequest](objects/RunCreateRequest.md) | [RunRecord](objects/RunRecord.md) | `internal_write` |
| [RunRuntime.control](interfaces/runtime--RunRuntime-control.md) | [RunControlRequest](objects/RunControlRequest.md) | [Acknowledgement](objects/Acknowledgement.md) | `internal_write` |
| [RunRuntime.checkpoint](interfaces/runtime--RunRuntime-checkpoint.md) | [RunsCheckpointRequest](objects/RunsCheckpointRequest.md) | [Checkpoint](objects/Checkpoint.md) | `internal_write` |
| [RunRuntime.resume](interfaces/runtime--RunRuntime-resume.md) | [RunsResumeRequest](objects/RunsResumeRequest.md) | [RunRecord](objects/RunRecord.md) | `internal_write` |
