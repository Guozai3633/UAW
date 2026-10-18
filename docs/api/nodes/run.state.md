# Run 与交互项 · 接口入口

[总覆盖图](../COVERAGE.md) · [详细设计](../../../docs/design/components/run-state.md)

计划代码：`src/uaw/run/state.py`。状态：完整节点仍按设计建设，已实现操作见下方接口及实施记录。

- [http · turns.submit](../interfaces/http--turns-submit.md)
- [http · runs.get](../interfaces/http--runs-get.md)
- [runtime · RunRuntime.create](../interfaces/runtime--RunRuntime-create.md)
- [http · runs.delivery.accept](../interfaces/http--runs-delivery-accept.md)
- [http · tasks.attach_conversation](../interfaces/http--tasks-attach-conversation.md)
- [component · run.state](../interfaces/component--run-state.md)
- [http · runs.conversation.get](../interfaces/http--runs-conversation-get.md)
- [http · runs.presentation.get](../interfaces/http--runs-presentation-get.md)
- [http · runs.clarification.get](../interfaces/http--runs-clarification-get.md)
- [http · runs.clarification.answer](../interfaces/http--runs-clarification-answer.md)
- [http · runs.correction.create](../interfaces/http--runs-correction-create.md)
- [http · runs.continuation.get](../interfaces/http--runs-continuation-get.md)
- [runtime · RunRuntime.commit_reply](../interfaces/runtime--RunRuntime-commit-reply.md)
- [runtime · RunRuntime.commit_question](../interfaces/runtime--RunRuntime-commit-question.md)
