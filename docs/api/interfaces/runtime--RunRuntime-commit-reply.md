# RunRuntime.commit_reply

状态：契约0.2，待实现。类别：Runtime 公共入口。所属：运行与会话。

消息完成候选，无Artifact/VerificationReport或用户接受字段。

[分类索引](../RUNTIME.md) · [统一规则](../CONVENTIONS.md) · [实际范围](../../implementation/README.md)

## 调用入口

计划Python异步签名：`async def commit_reply(request: ReplyProposal, context: TrustedExecutionContext) -> RuntimeRunruntimeCommitReplyResult`。所属入口为 `RunRuntime.commit_reply`。该签名是契约目标；实际方法定位见对应开发设计，不能从公网/LLM直接调用私有组件。

## 输入

[ReplyProposal](../objects/ReplyProposal.md)；每个字段的类型、必填性、默认注解、限制和分支见对象页。

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `protocol` | 常量 `conversation-v1` | 是 | 协议 |
| `run_ref` | [ConversationRunRef](../objects/ConversationRunRef.md) | 是 | 提议结束的原Run版本 |
| `input_revision` | [Revision](../objects/Revision.md) | 是 | 有效原文/补充版本 |
| `decision_record_ref` | [Ref](../objects/Ref.md) | 是 | 已登记FirstDecisionRecord |
| `text` | [NonEmptyText](../objects/NonEmptyText.md) | 是 | 实际原模型reply文本 |
| `source_refs` | 数组&lt;[Ref](../objects/Ref.md)&gt; | 是 | 已实际读取的用户材料/工具引用 |
| `unresolved_effect_refs` | 数组&lt;[Ref](../objects/Ref.md)&gt; | 是 | 消息终态依赖未决效果必须为空 |

## 输出

[RuntimeRunruntimeCommitReplyResult](../objects/RuntimeRunruntimeCommitReplyResult.md) 为完整返回结构。`kind=ok` 的payload是 [ReplyCommitReceipt](../objects/ReplyCommitReceipt.md)。`waiting`带wait_ref，其他非成功状态带Failure，不能用空对象假装成功。

| payload字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `protocol` | 常量 `conversation-v1` | 是 | 协议 |
| `run` | 见结构规则 | 是 | 实际completed Run |
| `item` | 见结构规则 | 是 | 实际消息Item |
| `input_revision` | [Revision](../objects/Revision.md) | 是 | 提交时输入版本 |
| `event_seq` | [Revision](../objects/Revision.md) | 是 | 最后持久事件位置 |

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
  "text": "example_001",
  "source_refs": [],
  "unresolved_effect_refs": []
}
```

## 成功结构示例

```json
{
  "kind": "ok",
  "payload": {
    "protocol": "conversation-v1",
    "run": {
      "id": "example_001",
      "task_id": "example_001",
      "conversation_id": "example_001",
      "revision": 0,
      "status": "completed",
      "budget": {
        "limits": {
          "input_tokens": 0,
          "output_tokens": 0,
          "model_calls": 0,
          "tool_calls": 0,
          "child_agents": 0,
          "wall_time_ms": 0,
          "money": "0",
          "currency": "CNY"
        },
        "max_steps": 0,
        "max_depth": 0,
        "deadline": "2026-10-07T02:00:00Z"
      },
      "created_at": "2026-10-07T02:00:00Z",
      "outcome": "succeeded"
    },
    "item": {
      "id": "example_001",
      "conversation_id": "example_001",
      "type": "agent_message",
      "status": "completed",
      "revision": 0,
      "text": "example_001",
      "resource_refs": [],
      "created_at": "2026-10-07T02:00:00Z",
      "updated_at": "2026-10-07T02:00:00Z",
      "run_id": "example_001"
    },
    "input_revision": 1,
    "event_seq": 1
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
| `agent.loop` | [开发设计](../../../docs/design/components/agent-loop.md) | `src/uaw/agent/loop.py` |

[接口机器目录](../../../contracts/interfaces.json) · [统一对象schema](../../../contracts/uaw.schema.json)
