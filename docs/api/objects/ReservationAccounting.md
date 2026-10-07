# ReservationAccounting

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：运行与会话。

每个attempt独占预留；发出调用意图后保留未知用量。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `run_id` | [ID](./ID.md) | 是 | 运行 | 类型约束见对应对象 |
| `operation_id` | [ID](./ID.md) | 是 | 操作 | 类型约束见对应对象 |
| `trace_id` | [ID](./ID.md) | 是 | 链路 | 类型约束见对应对象 |
| `attempt_id` | [ID](./ID.md) | 是 | 尝试 | 类型约束见对应对象 |
| `deadline` | [Timestamp](./Timestamp.md) | 是 | 预留截止 | 类型约束见对应对象 |
| `dispatched` | [Bool](./Bool.md) | 是 | 已经提交调用意图 | 类型约束见对应对象 |
| `held` | [ResourceVector](./ResourceVector.md) | 是 | 待确认额度 | 类型约束见对应对象 |
| `used` | [ResourceVector](./ResourceVector.md) | 是 | 已观察消耗 | 类型约束见对应对象 |
| `billing_pending` | [Bool](./Bool.md) | 是 | 账单待确认 | 类型约束见对应对象 |
| `usage` | [Usage](./Usage.md) | 否 | 最近实际观察 | 类型约束见对应对象 |
| `usage_revision` | [Revision](./Revision.md) | 否 | 用量修订 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## dependentRequired结构规则

```json
{
  "dependentRequired": {
    "usage": [
      "usage_revision"
    ],
    "usage_revision": [
      "usage"
    ]
  }
}
```

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "run_id": "example_001",
  "operation_id": "example_001",
  "trace_id": "example_001",
  "attempt_id": "example_001",
  "deadline": "2026-10-07T02:00:00Z",
  "dispatched": true,
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
  "billing_pending": true
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.ReservationAccounting`。
