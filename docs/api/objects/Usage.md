# Usage

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：模型调用。

一次attempt实际或待核对用量。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `attempt_id` | [ID](./ID.md) | 是 | 真实尝试ID | 类型约束见对应对象 |
| `resources` | [MeasuredResources](./MeasuredResources.md) | 是 | 真实观察值；未知项省略。 | 类型约束见对应对象 |
| `billing_state` | enum: `confirmed` / `estimated` / `pending` | 是 | 账单确定程度 | — |
| `provider_receipt_id` | [ID](./ID.md) | 否 | 去重账单回执 | 类型约束见对应对象 |
| `cached_input_tokens` | [Count](./Count.md) | 否 | 供应商实际报告缓存输入 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## allOf结构规则

```json
{
  "allOf": [
    {
      "if": {
        "properties": {
          "billing_state": {
            "enum": [
              "confirmed",
              "estimated"
            ]
          }
        },
        "required": [
          "billing_state"
        ]
      },
      "then": {
        "properties": {
          "resources": {
            "required": [
              "input_tokens",
              "output_tokens",
              "money"
            ]
          }
        }
      }
    },
    {
      "if": {
        "properties": {
          "billing_state": {
            "const": "pending"
          }
        },
        "required": [
          "billing_state"
        ]
      },
      "then": {
        "properties": {
          "resources": {
            "not": {
              "required": [
                "money"
              ]
            }
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
  "attempt_id": "example_001",
  "resources": {
    "model_calls": 0,
    "tool_calls": 0,
    "child_agents": 0,
    "wall_time_ms": 0,
    "currency": "CNY",
    "input_tokens": 0,
    "output_tokens": 0,
    "money": "0"
  },
  "billing_state": "confirmed"
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.Usage`。
