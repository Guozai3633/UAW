# ToolReconciliationReceipt

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：工具运行。

可信提供方的固定动作核对回执，不能由模型或超时推测构造。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `action_ref` | [Ref](./Ref.md) | 是 | 固定动作 | 类型约束见对应对象 |
| `attempt_id` | [ID](./ID.md) | 是 | 实际尝试 | 类型约束见对应对象 |
| `provider_ref` | [Ref](./Ref.md) | 是 | 固定提供方 | 类型约束见对应对象 |
| `receipt_ref` | [Ref](./Ref.md) | 是 | 当前读取回执 | 类型约束见对应对象 |
| `outcome` | [ReconciliationOutcome](./ReconciliationOutcome.md) | 是 | 效果结论 | 类型约束见对应对象 |
| `evidence_refs` | 数组&lt;[Ref](./Ref.md)&gt; | 是 | 可重新读取的证明 | 最少项 `0`；最多项 `256` |
| `usage` | [Usage](./Usage.md) | 是 | 实际或待核对消耗 | 类型约束见对应对象 |
| `observed_at` | [Timestamp](./Timestamp.md) | 是 | 观察时间 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## allOf结构规则

```json
{
  "allOf": [
    {
      "if": {
        "properties": {
          "outcome": {
            "enum": [
              "applied",
              "not_applied"
            ]
          }
        },
        "required": [
          "outcome"
        ]
      },
      "then": {
        "properties": {
          "evidence_refs": {
            "minItems": 1
          }
        }
      }
    }
  ]
}
```

## 运行时约束

- Reader校验真实来源、主体、签名/完整性和固定版本；调用方比较action/attempt/provider/receipt，并核对usage.attempt_id。
- applied/not_applied必须有证据；not_applied不代表零用量或允许重发；unknown保留额度，不从超时或未记dispatch推导未执行。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "action_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "attempt_id": "example_001",
  "provider_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "receipt_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "outcome": "applied",
  "evidence_refs": [
    {
      "kind": "web",
      "id": "example_001",
      "version": "example_001"
    }
  ],
  "usage": {
    "attempt_id": "example_001",
    "resources": {
      "currency": "CNY",
      "input_tokens": 0,
      "output_tokens": 0,
      "model_calls": 0,
      "tool_calls": 0,
      "child_agents": 0,
      "wall_time_ms": 0,
      "money": "0"
    },
    "billing_state": "confirmed"
  },
  "observed_at": "2026-10-07T02:00:00Z"
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.ToolReconciliationReceipt`。
