# RunPresentationUnderstanding

状态：对象契约0.2 / conversation-v1；可用范围见具体接口与实施记录。所属：运行与会话。

同次真实模型决策的理解提示，独立于不可变执行帧。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `state` | enum: `pending` / `available` / `not_provided` | 是 | 尚未得到决策、有原理解或本次未提供 | — |
| `input_revision` | [Revision](./Revision.md) | 是 | 本次读取的当前输入版本 | ≥ `1`；类型约束见对应对象 |
| `value` | [ConversationUnderstanding](./ConversationUnderstanding.md) | 否 | 真实模型摘要和假设；没有时省略 | 类型约束见对应对象 |
| `decision_record_ref` | [Ref](./Ref.md) | 否 | 原FirstDecisionRecord及摘要 | 类型约束见对应对象 |
| `model_output_ref` | [Ref](./Ref.md) | 否 | 原ModelOutput版本 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## allOf结构规则

```json
{
  "allOf": [
    {
      "if": {
        "properties": {
          "state": {
            "const": "available"
          }
        },
        "required": [
          "state"
        ]
      },
      "then": {
        "required": [
          "value",
          "decision_record_ref",
          "model_output_ref"
        ]
      },
      "else": {
        "not": {
          "anyOf": [
            {
              "required": [
                "value"
              ]
            },
            {
              "required": [
                "decision_record_ref"
              ]
            },
            {
              "required": [
                "model_output_ref"
              ]
            }
          ]
        }
      }
    }
  ]
}
```

## 运行时约束

- available必须绑定同Run/当前input_revision的原决策及成功ModelOutput；不改TaskFrame或补造理解。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "state": "pending",
  "input_revision": 1
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.RunPresentationUnderstanding`。
