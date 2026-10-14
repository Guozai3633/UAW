# RunInputPatch

状态：对象契约0.2 / conversation-v1；可用范围见具体接口与实施记录。所属：运行与会话。

追加输入关联，InputRecord结构不变；受理与生效区分。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `protocol` | 常量 `conversation-v1` | 是 | 协议 | — |
| `run_id` | [ID](./ID.md) | 是 | 原Run | 类型约束见对应对象 |
| `conversation_id` | [ID](./ID.md) | 是 | 会话 | 类型约束见对应对象 |
| `request_id` | [ID](./ID.md) | 是 | 原用户逻辑请求 | 类型约束见对应对象 |
| `input_ref` | [UserInputRef](./UserInputRef.md) | 是 | 原子追加的实际InputRecord | 类型约束见对应对象 |
| `kind` | enum: `clarification_answer` / `correction` | 是 | 来源类型 | — |
| `base_input_revision` | [Revision](./Revision.md) | 是 | 原有效输入版本 | ≥ `1`；类型约束见对应对象 |
| `input_revision` | [Revision](./Revision.md) | 是 | 受理后有效输入版本 | ≥ `1`；类型约束见对应对象 |
| `question_item_id` | [ID](./ID.md) | 否 | 澄清时必需；纠正时不允许 | 类型约束见对应对象 |
| `question_revision` | [Revision](./Revision.md) | 否 | 原提问版本，与Item关联 | ≥ `1`；类型约束见对应对象 |
| `state` | enum: `accepted` / `applied` / `superseded` / `cancelled` | 是 | 受理/真实生效 | — |
| `created_at` | [Timestamp](./Timestamp.md) | 是 | 受理时间 | 类型约束见对应对象 |
| `applied_at` | [Timestamp](./Timestamp.md) | 否 | 实际安全边界生效时刻 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## allOf结构规则

```json
{
  "allOf": [
    {
      "if": {
        "properties": {
          "kind": {
            "const": "clarification_answer"
          }
        },
        "required": [
          "kind"
        ]
      },
      "then": {
        "required": [
          "question_item_id",
          "question_revision"
        ]
      },
      "else": {
        "not": {
          "anyOf": [
            {
              "required": [
                "question_item_id"
              ]
            },
            {
              "required": [
                "question_revision"
              ]
            }
          ]
        }
      }
    },
    {
      "if": {
        "properties": {
          "state": {
            "const": "applied"
          }
        },
        "required": [
          "state"
        ]
      },
      "then": {
        "required": [
          "applied_at"
        ]
      },
      "else": {
        "not": {
          "required": [
            "applied_at"
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
  "request_id": "example_001",
  "input_ref": {
    "kind": "input",
    "id": "example_001",
    "version": "example_001"
  },
  "kind": "clarification_answer",
  "base_input_revision": 1,
  "input_revision": 1,
  "state": "accepted",
  "created_at": "2026-10-07T02:00:00Z",
  "question_item_id": "example_001",
  "question_revision": 1
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.RunInputPatch`。
