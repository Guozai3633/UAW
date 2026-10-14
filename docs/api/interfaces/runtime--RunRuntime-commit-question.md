# RunRuntime.commit_question

状态：契约0.2，待实现。类别：Runtime 公共入口。所属：运行与会话。

服务从实际ask动作创建的问题提交候选，不是用户授权。

[分类索引](../RUNTIME.md) · [统一规则](../CONVENTIONS.md) · [实际范围](../../implementation/README.md)

## 调用入口

计划Python异步签名：`async def commit_question(request: ClarificationProposal, context: TrustedExecutionContext) -> RuntimeRunruntimeCommitQuestionResult`。所属入口为 `RunRuntime.commit_question`。该签名是契约目标；实际方法定位见对应开发设计，不能从公网/LLM直接调用私有组件。

## 输入

[ClarificationProposal](../objects/ClarificationProposal.md)；每个字段的类型、必填性、默认注解、限制和分支见对象页。

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `protocol` | 常量 `conversation-v1` | 是 | 协议 |
| `run_ref` | [ConversationRunRef](../objects/ConversationRunRef.md) | 是 | 原Run预期版本 |
| `input_revision` | [Revision](../objects/Revision.md) | 是 | 原有效输入版本 |
| `decision_record_ref` | [Ref](../objects/Ref.md) | 是 | 服务登记的原ask模型回执 |
| `prompt` | [ClarificationPrompt](../objects/ClarificationPrompt.md) | 是 | 须与实际ask输出一致 |

## 输出

[RuntimeRunruntimeCommitQuestionResult](../objects/RuntimeRunruntimeCommitQuestionResult.md) 为完整返回结构。`kind=ok` 的payload是 [ClarificationView](../objects/ClarificationView.md)。`waiting`带wait_ref，其他非成功状态带Failure，不能用空对象假装成功。

| payload字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `question` | [ClarificationQuestion](../objects/ClarificationQuestion.md) | 是 | 当前实际问题 |
| `run_revision` | [Revision](../objects/Revision.md) | 是 | 当前Run版本，用于提交CAS |
| `run_status` | [RunStatus](../objects/RunStatus.md) | 是 | 当前Run真实状态 |
| `input_revision` | [Revision](../objects/Revision.md) | 是 | 当前有效输入版本 |

## 约束与提交

- 效果分类：`internal_write`。
- 认证/上下文：`service`；范围及权限由服务端或Runner取得。
- 请求/动作ID去重与CAS按[统一规则](../CONVENTIONS.md)执行，重复ID不同参数必须冲突。
- 仅可信服务port；未装配时明确不可用。模型来源与当前Run/输入/权限/预算/取消由服务复核。
- 首次动作不能直接结束Run；消息完成不要求Artifact，但原Tool效果账本不能仅信任空候选列表。

## 错误、等待、取消

错误对象是 [Failure](../objects/Failure.md)；统一分类：schema_invalid / permission_denied / feature_disabled / revision_conflict / stale_resource / dependency_unavailable / budget_exceeded / deadline_exceeded / cancelled / unknown_effect。实际Runtime需要把业务错误映射到此对象；上述分类不会代替明确failed_phase和恢复提示。

只读可在有界策略内重试；写失败先核对动作账本，效果unknown时禁止盲重试；waiting通过审批决定、用户输入、process.poll或agents.wait推进。取消只停止后续执行，已有效果如实保留。

## 请求示例

示例展示结构；不代表这些示例引用存在。

```json
{
  "protocol": "conversation-v1",
  "run_ref": {
    "kind": "run",
    "id": "example_001",
    "version": "example_001"
  },
  "input_revision": 1,
  "decision_record_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "prompt": {
    "text": "example_001",
    "reason": "example_001",
    "options": []
  }
}
```

## 成功结构示例

```json
{
  "kind": "ok",
  "payload": {
    "question": {
      "protocol": "conversation-v1",
      "run_id": "example_001",
      "conversation_id": "example_001",
      "item_id": "example_001",
      "revision": 1,
      "input_revision": 1,
      "prompt": {
        "text": "example_001",
        "reason": "example_001",
        "options": []
      },
      "decision_record_ref": {
        "kind": "web",
        "id": "example_001",
        "version": "example_001"
      },
      "state": "open",
      "created_at": "2026-10-07T02:00:00Z"
    },
    "run_revision": 1,
    "run_status": "waiting_for_user",
    "input_revision": 1
  },
  "output_refs": []
}
```

## 拒绝结构示例

```json
{
  "kind": "denied",
  "output_refs": [],
  "failure": {
    "code": "permission_denied",
    "category": "authorization",
    "message": "当前主体没有本动作所需权限。",
    "retryable": false,
    "failed_phase": "policy_gate",
    "recover_hint": "取得真实授权后重新检查；不能通过换工具绕过。"
  }
}
```

## 模块与目录

| 节点 | 详细策略 | 计划代码位置 |
| --- | --- | --- |
| `run.state` | [开发设计](../../../docs/design/components/run-state.md) | `src/uaw/run/state.py` |
| `run.history` | [开发设计](../../../docs/design/components/run-history.md) | `src/uaw/run/history.py` |
| `run.budget` | [开发设计](../../../docs/design/components/run-budget.md) | `src/uaw/run/budget.py` |
| `intent.ambiguity` | [开发设计](../../../docs/design/components/intent-ambiguity.md) | `src/uaw/intent/ambiguity.py` |

[接口机器目录](../../../contracts/interfaces.json) · [统一对象schema](../../../contracts/uaw.schema.json)
