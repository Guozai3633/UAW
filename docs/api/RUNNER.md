# 本地 Runner 协议

[接口总入口](README.md)。状态：设计契约0.1。

| 接口 | 输入 | 成功payload | 效果 |
| --- | --- | --- | --- |
| [pair.begin](interfaces/runner--pair-begin.md) | [RunnerPairBeginRequest](objects/RunnerPairBeginRequest.md) | [RunnerPairing](objects/RunnerPairing.md) | `credential` |
| [pair.complete](interfaces/runner--pair-complete.md) | [RunnerPairCompleteRequest](objects/RunnerPairCompleteRequest.md) | [RunnerDevice](objects/RunnerDevice.md) | `credential` |
| [heartbeat](interfaces/runner--heartbeat.md) | [RunnerHeartbeatRequest](objects/RunnerHeartbeatRequest.md) | [RunnerDevice](objects/RunnerDevice.md) | `read` |
| [root.select](interfaces/runner--root-select.md) | [RunnerRootSelectRequest](objects/RunnerRootSelectRequest.md) | [RootSelection](objects/RootSelection.md) | `credential` |
| [workspace.capture](interfaces/runner--workspace-capture.md) | [CaptureRequest](objects/CaptureRequest.md) | [BaseState](objects/BaseState.md) | `read` |
| [workspace.allocate](interfaces/runner--workspace-allocate.md) | [WorkspaceSpec](objects/WorkspaceSpec.md) | [WorkspaceRecord](objects/WorkspaceRecord.md) | `internal_write` |
| [environment.inspect](interfaces/runner--environment-inspect.md) | [ToolEnvironmentInspectInput](objects/ToolEnvironmentInspectInput.md) | [EnvironmentRecord](objects/EnvironmentRecord.md) | `read` |
| [environment.ensure](interfaces/runner--environment-ensure.md) | [ToolEnvironmentEnsureInput](objects/ToolEnvironmentEnsureInput.md) | [EnvironmentRecord](objects/EnvironmentRecord.md) | `process` |
| [file.read](interfaces/runner--file-read.md) | [ToolFileReadInput](objects/ToolFileReadInput.md) | [FileContent](objects/FileContent.md) | `read` |
| [file.write](interfaces/runner--file-write.md) | [ToolFileWriteInput](objects/ToolFileWriteInput.md) | [ChangeSet](objects/ChangeSet.md) | `workspace_write` |
| [file.list](interfaces/runner--file-list.md) | [WorkspacesFilesRequest](objects/WorkspacesFilesRequest.md) | [FilePage](objects/FilePage.md) | `read` |
| [process.exec](interfaces/runner--process-exec.md) | [ToolProcessExecInput](objects/ToolProcessExecInput.md) | [ProcessRecord](objects/ProcessRecord.md) | `process` |
| [process.poll](interfaces/runner--process-poll.md) | [ToolProcessPollInput](objects/ToolProcessPollInput.md) | [ProcessRecord](objects/ProcessRecord.md) | `read` |
| [process.stop](interfaces/runner--process-stop.md) | [ToolProcessStopInput](objects/ToolProcessStopInput.md) | [ProcessRecord](objects/ProcessRecord.md) | `process` |
| [changes.capture](interfaces/runner--changes-capture.md) | [ToolWorkspaceChangesInput](objects/ToolWorkspaceChangesInput.md) | [ChangeSet](objects/ChangeSet.md) | `read` |
| [changes.merge](interfaces/runner--changes-merge.md) | [WorkspacesMergeRequest](objects/WorkspacesMergeRequest.md) | [MergeResult](objects/MergeResult.md) | `workspace_write` |
| [changes.revert](interfaces/runner--changes-revert.md) | [WorkspacesRevertRequest](objects/WorkspacesRevertRequest.md) | [MergeResult](objects/MergeResult.md) | `workspace_write` |
| [workspace.release](interfaces/runner--workspace-release.md) | [RefRequest](objects/RefRequest.md) | [Acknowledgement](objects/Acknowledgement.md) | `internal_write` |
