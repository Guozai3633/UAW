# ClarificationView

状态：对象契约0.2 / conversation-v1；可用范围见具体接口与实施记录。所属：运行与会话。

UI同源读取原问题与Run，刷新不创建新launch或会话。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `question` | [ClarificationQuestion](./ClarificationQuestion.md) | 是 | 当前实际问题 | 类型约束见对应对象 |
| `run_revision` | [Revision](./Revision.md) | 是 | 当前Run版本，用于提交CAS | ≥ `1`；类型约束见对应对象 |
| `run_status` | [RunStatus](./RunStatus.md) | 是 | 当前Run真实状态 | 类型约束见对应对象 |
| `input_revision` | [Revision](./Revision.md) | 是 | 当前有效输入版本 | ≥ `1`；类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## allOf结构规则

```json
{
  "allOf": [
    {
      "if": {
        "properties": {
          "question": {
            "properties": {
              "state": {
                "const": "open"
              }
            },
            "required": [
              "state"
            ]
          }
        },
        "required": [
          "question"
        ]
      },
      "then": {
        "properties": {
          "run_status": {
            "const": "waiting_for_user"
          }
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
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.ClarificationView`。
