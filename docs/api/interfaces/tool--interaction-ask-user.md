# interaction.ask_user

状态：契约0.1，待实现。类别：模型可调用工具。所属：运行与会话。

提出必要澄清并挂起等待。

[分类索引](../TOOL.md) · [统一规则](../CONVENTIONS.md) · [实际范围](../../implementation/README.md)

## 调用入口

LLM提出 `interaction.ask_user(arguments)` → ToolRuntime校验/权限/必要审批 → `run`负责人。ToolRuntime注入可信上下文，业务参数只使用下方输入结构。

## 输入

[ToolInteractionAsk_userInput](../objects/ToolInteractionAsk_userInput.md)；每个字段的类型、必填性、默认注解、限制和分支见对象页。

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `question` | [NonEmptyText](../objects/NonEmptyText.md) | 是 | 自包含问题 |
| `options` | 数组&lt;[NonEmptyText](../objects/NonEmptyText.md)&gt; | 否 | 简短选项 |
| `blocking` | [Bool](../objects/Bool.md) | 是 | 答案是否执行前提 |

## 输出

[ToolInteractionAskUserResult](../objects/ToolInteractionAskUserResult.md) 为完整返回结构。`kind=ok` 的payload是 [InteractionItem](../objects/InteractionItem.md)。`waiting`带wait_ref，其他非成功状态带Failure，不能用空对象假装成功。

| payload字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `id` | [ID](../objects/ID.md) | 是 | 交互项 |
| `conversation_id` | [ID](../objects/ID.md) | 是 | 会话 |
| `run_id` | [ID](../objects/ID.md) | 否 | 运行 |
| `type` | [ItemType](../objects/ItemType.md) | 是 | 消息/工具/文件/审批等 |
| `status` | [ItemStatus](../objects/ItemStatus.md) | 是 | 交互状态 |
| `revision` | [Revision](../objects/Revision.md) | 是 | 项版本 |
| `text` | [Text](../objects/Text.md) | 是 | 可见内容 |
| `resource_refs` | 数组&lt;[Ref](../objects/Ref.md)&gt; | 是 | 关联真实资源 |
| `created_at` | [Timestamp](../objects/Timestamp.md) | 是 | 开始 |
| `updated_at` | [Timestamp](../objects/Timestamp.md) | 是 | 最近更新 |

## 约束与提交

- 效果分类：`internal_write`。
- 认证/上下文：`agent`；范围及权限由服务端或Runner取得。
- 请求/动作ID去重与CAS按[统一规则](../CONVENTIONS.md)执行，重复ID不同参数必须冲突。
- 批准动作走ApprovalRequest；澄清不能伪造授权，超时不等于答案。

## 错误、等待、取消

错误对象是 [Failure](../objects/Failure.md)；统一分类：schema_invalid / permission_denied / feature_disabled / revision_conflict / stale_resource / dependency_unavailable / budget_exceeded / deadline_exceeded / cancelled / unknown_effect。实际Runtime需要把业务错误映射到此对象；上述分类不会代替明确failed_phase和恢复提示。

只读可在有界策略内重试；写失败先核对动作账本，效果unknown时禁止盲重试；waiting通过审批决定、用户输入、process.poll或agents.wait推进。取消只停止后续执行，已有效果如实保留。

## 请求示例

示例展示结构；不代表这些示例引用存在。

```json
{
  "question": "example_001",
  "blocking": true
}
```

## 成功结构示例

```json
{
  "kind": "ok",
  "payload": {
    "id": "example_001",
    "conversation_id": "example_001",
    "type": "user_message",
    "status": "pending",
    "revision": 0,
    "text": "example_001",
    "resource_refs": [],
    "created_at": "2026-10-07T02:00:00Z",
    "updated_at": "2026-10-07T02:00:00Z"
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
| `run.approval` | [开发设计](../../../docs/design/components/run-approval.md) | `src/uaw/run/approval.py` |
| `intent.ambiguity` | [开发设计](../../../docs/design/components/intent-ambiguity.md) | `src/uaw/intent/ambiguity.py` |

[接口机器目录](../../../contracts/interfaces.json) · [统一对象schema](../../../contracts/uaw.schema.json)
