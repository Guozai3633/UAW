# ClarificationQuestion

状态：对象契约0.2 / conversation-v1；可用范围见具体接口与实施记录。所属：运行与会话。

原问题的持久权威关联，用稳定Item表达，无新RefKind。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `protocol` | 常量 `conversation-v1` | 是 | 协议 | — |
| `run_id` | [ID](./ID.md) | 是 | 原Run | 类型约束见对应对象 |
| `conversation_id` | [ID](./ID.md) | 是 | 所属会话 | 类型约束见对应对象 |
| `item_id` | [ID](./ID.md) | 是 | agent_message问题Item | 类型约束见对应对象 |
| `revision` | [Revision](./Revision.md) | 是 | 问题CAS版本 | ≥ `1`；类型约束见对应对象 |
| `input_revision` | [Revision](./Revision.md) | 是 | 提问时有效原文版本 | ≥ `1`；类型约束见对应对象 |
| `prompt` | [ClarificationPrompt](./ClarificationPrompt.md) | 是 | 用户看到的问题 | 类型约束见对应对象 |
| `decision_record_ref` | [Ref](./Ref.md) | 是 | 原ask动作的实际模型记录 | 类型约束见对应对象 |
| `state` | enum: `open` / `answered` / `stale` / `cancelled` | 是 | 问题状态 | — |
| `created_at` | [Timestamp](./Timestamp.md) | 是 | 问题提交时间 | 类型约束见对应对象 |
| `answer_input_ref` | [UserInputRef](./UserInputRef.md) | 否 | 实际受理答复，answered时必需 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## allOf结构规则

```json
{
  "allOf": [
    {
      "if": {
        "properties": {
          "state": {
            "const": "answered"
          }
        },
        "required": [
          "state"
        ]
      },
      "then": {
        "required": [
          "answer_input_ref"
        ]
      },
      "else": {
        "not": {
          "required": [
            "answer_input_ref"
          ]
        }
      }
    }
  ]
}
```

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
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
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.ClarificationQuestion`。
