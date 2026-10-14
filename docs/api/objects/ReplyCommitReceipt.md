# ReplyCommitReceipt

状态：对象契约0.2 / conversation-v1；可用范围见具体接口与实施记录。所属：运行与会话。

消息与Run/Event原子提交的服务回执。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `protocol` | 常量 `conversation-v1` | 是 | 协议 | — |
| `run` | 见结构规则 | 是 | 实际completed Run | — |
| `item` | 见结构规则 | 是 | 实际消息Item | — |
| `input_revision` | [Revision](./Revision.md) | 是 | 提交时输入版本 | ≥ `1`；类型约束见对应对象 |
| `event_seq` | [Revision](./Revision.md) | 是 | 最后持久事件位置 | ≥ `1`；类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
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
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.ReplyCommitReceipt`。
