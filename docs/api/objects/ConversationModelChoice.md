# ConversationModelChoice

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：模型调用。

用户选择当前会话模型；无法选inherit。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `mode` | [ConversationModelMode](./ConversationModelMode.md) | 是 | explicit或auto | 类型约束见对应对象 |
| `model_id` | [ID](./ID.md) | 否 | 固定模型ID | 类型约束见对应对象 |
| `allowed_model_ids` | 数组&lt;[ID](./ID.md)&gt; | 否 | Auto授权范围 | 最少项 `0`；最多项 `256` |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## allOf结构规则

```json
{
  "allOf": [
    {
      "if": {
        "properties": {
          "mode": {
            "const": "explicit"
          }
        },
        "required": [
          "mode"
        ]
      },
      "then": {
        "required": [
          "model_id"
        ],
        "not": {
          "required": [
            "allowed_model_ids"
          ]
        }
      }
    },
    {
      "if": {
        "properties": {
          "mode": {
            "const": "auto"
          }
        },
        "required": [
          "mode"
        ]
      },
      "then": {
        "required": [
          "allowed_model_ids"
        ],
        "properties": {
          "allowed_model_ids": {
            "minItems": 1
          }
        },
        "not": {
          "required": [
            "model_id"
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
  "mode": "explicit",
  "model_id": "example_001"
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.ConversationModelChoice`。
