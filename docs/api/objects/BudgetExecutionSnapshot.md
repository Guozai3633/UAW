# BudgetExecutionSnapshot

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：运行与会话。

单次MVCC读取的预算执行状态，保留未知费用语义。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `ledger` | [RootBudgetLedger](./RootBudgetLedger.md) | 是 | 当前根预算 | 类型约束见对应对象 |
| `reservation` | [BudgetReservation](./BudgetReservation.md) | 是 | 原尝试预留 | 类型约束见对应对象 |
| `attempt` | [BudgetAttemptState](./BudgetAttemptState.md) | 是 | 原尝试状态 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "ledger": {
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
  },
  "reservation": {
    "id": "example_001",
    "estimates": {
      "input_tokens": 0,
      "output_tokens": 0,
      "model_calls": 0,
      "tool_calls": 0,
      "child_agents": 0,
      "wall_time_ms": 0,
      "money": "0",
      "currency": "CNY"
    },
    "settled_usage_refs": [],
    "status": "reserved",
    "revision": 0
  },
  "attempt": {
    "run_id": "example_001",
    "operation_id": "example_001",
    "trace_id": "example_001",
    "attempt_id": "example_001",
    "reservation_ref": {
      "kind": "web",
      "id": "example_001",
      "version": "example_001"
    },
    "deadline": "2026-10-07T02:00:00Z",
    "dispatched": true
  }
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.BudgetExecutionSnapshot`。
