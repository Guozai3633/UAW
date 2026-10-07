# agents.message

状态：契约0.1，待实现。类别：模型可调用工具。所属：Agent执行与协作。

向当前任务的子Agent发送协作资料。

[分类索引](../TOOL.md) · [统一规则](../CONVENTIONS.md) · [实际范围](../../implementation/README.md)

## 调用入口

LLM提出 `agents.message(arguments)` → ToolRuntime校验/权限/必要审批 → `agent`负责人。ToolRuntime注入可信上下文，业务参数只使用下方输入结构。

## 输入

[ToolAgentsMessageInput](../objects/ToolAgentsMessageInput.md)；每个字段的类型、必填性、默认注解、限制和分支见对象页。

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `to_agent_ref` | [Ref](../objects/Ref.md) | 是 | 接收实例 |
| `message_id` | [ID](../objects/ID.md) | 是 | 去重键 |
| `text` | [Text](../objects/Text.md) | 是 | 信息 |
| `payload_refs` | 数组&lt;[Ref](../objects/Ref.md)&gt; | 是 | 获准资料 |

## 输出

[ToolAgentsMessageResult](../objects/ToolAgentsMessageResult.md) 为完整返回结构。`kind=ok` 的payload是 [AgentMessage](../objects/AgentMessage.md)。`waiting`带wait_ref，其他非成功状态带Failure，不能用空对象假装成功。

| payload字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `message_id` | [ID](../objects/ID.md) | 是 | 通道去重键 |
| `from_ref` | [Ref](../objects/Ref.md) | 是 | 发送实例 |
| `to_ref` | [Ref](../objects/Ref.md) | 是 | 接收实例 |
| `task_revision` | [Revision](../objects/Revision.md) | 是 | 共同任务基线 |
| `text` | [Text](../objects/Text.md) | 是 | 协作内容 |
| `payload_refs` | 数组&lt;[Ref](../objects/Ref.md)&gt; | 是 | 共享资料/候选结果 |
| `created_at` | [Timestamp](../objects/Timestamp.md) | 是 | 提交时间 |

## 约束与提交

- 效果分类：`internal_write`。
- 认证/上下文：`agent`；范围及权限由服务端或Runner取得。
- 请求/动作ID去重与CAS按[统一规则](../CONVENTIONS.md)执行，重复ID不同参数必须冲突。
- 实例树内授权；不能向不相关用户会话发送消息。

## 错误、等待、取消

错误对象是 [Failure](../objects/Failure.md)；统一分类：schema_invalid / permission_denied / feature_disabled / revision_conflict / stale_resource / dependency_unavailable / budget_exceeded / deadline_exceeded / cancelled / unknown_effect。实际Runtime需要把业务错误映射到此对象；上述分类不会代替明确failed_phase和恢复提示。

只读可在有界策略内重试；写失败先核对动作账本，效果unknown时禁止盲重试；waiting通过审批决定、用户输入、process.poll或agents.wait推进。取消只停止后续执行，已有效果如实保留。

## 请求示例

示例展示结构；不代表这些示例引用存在。

```json
{
  "to_agent_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "message_id": "example_001",
  "text": "example_001",
  "payload_refs": []
}
```

## 成功结构示例

```json
{
  "kind": "ok",
  "payload": {
    "message_id": "example_001",
    "from_ref": {
      "kind": "web",
      "id": "example_001",
      "version": "example_001"
    },
    "to_ref": {
      "kind": "web",
      "id": "example_001",
      "version": "example_001"
    },
    "task_revision": 0,
    "text": "example_001",
    "payload_refs": [],
    "created_at": "2026-10-07T02:00:00Z"
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
| `agent.collaboration.channel` | [开发设计](../../../docs/design/components/agent-collaboration-channel.md) | `src/uaw/agent/collaboration/channel.py` |

[接口机器目录](../../../contracts/interfaces.json) · [统一对象schema](../../../contracts/uaw.schema.json)
