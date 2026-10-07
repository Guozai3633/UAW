# ProviderReceipt

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：工具运行。

适配器原始结果指针，业务语义交规范器。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `attempt_id` | [ID](./ID.md) | 是 | 实际尝试 | 类型约束见对应对象 |
| `raw_result_ref` | [Ref](./Ref.md) | 是 | 原始响应 | 类型约束见对应对象 |
| `transport_status` | [NonEmptyText](./NonEmptyText.md) | 是 | 传输状态 | 类型约束见对应对象 |
| `effect_state` | [EffectState](./EffectState.md) | 是 | 效果确定性 | 类型约束见对应对象 |
| `usage` | [Usage](./Usage.md) | 是 | 实际用量 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "attempt_id": "example_001",
  "raw_result_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "transport_status": "example_001",
  "effect_state": "confirmed",
  "usage": {
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
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.ProviderReceipt`。
