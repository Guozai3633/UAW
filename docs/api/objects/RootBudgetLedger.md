# RootBudgetLedger

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：运行与会话。

根预算的事务权威；所有attempt与待核对额度保留。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `id` | [ID](./ID.md) | 是 | 账本 | 类型约束见对应对象 |
| `run_id` | [ID](./ID.md) | 是 | 运行 | 类型约束见对应对象 |
| `revision` | [Revision](./Revision.md) | 是 | CAS | 类型约束见对应对象 |
| `limits` | [ResourceVector](./ResourceVector.md) | 是 | 总额 | 类型约束见对应对象 |
| `held` | [ResourceVector](./ResourceVector.md) | 是 | 尚未确认的额度 | 类型约束见对应对象 |
| `used` | [ResourceVector](./ResourceVector.md) | 是 | 已观察消耗 | 类型约束见对应对象 |
| `billing_pending` | [Bool](./Bool.md) | 是 | 待确认 | 类型约束见对应对象 |
| `overdrawn` | [Bool](./Bool.md) | 是 | 实际超额 | 类型约束见对应对象 |
| `cancel_requested` | [Bool](./Bool.md) | 是 | 停止新准入 | 类型约束见对应对象 |
| `deadline` | [Timestamp](./Timestamp.md) | 是 | 截止 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "id": "example_001",
  "run_id": "example_001",
  "revision": 0,
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
  "held": {
    "input_tokens": 0,
    "output_tokens": 0,
    "model_calls": 0,
    "tool_calls": 0,
    "child_agents": 0,
    "wall_time_ms": 0,
    "money": "0",
    "currency": "CNY"
  },
  "used": {
    "input_tokens": 0,
    "output_tokens": 0,
    "model_calls": 0,
    "tool_calls": 0,
    "child_agents": 0,
    "wall_time_ms": 0,
    "money": "0",
    "currency": "CNY"
  },
  "billing_pending": true,
  "overdrawn": true,
  "cancel_requested": true,
  "deadline": "2026-10-07T02:00:00Z"
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.RootBudgetLedger`。
