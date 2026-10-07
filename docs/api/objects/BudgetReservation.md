# BudgetReservation

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：运行与会话。

所有重试和子Agent共享父预算账本。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `id` | [ID](./ID.md) | 是 | 预留 | 类型约束见对应对象 |
| `parent_ref` | [Ref](./Ref.md) | 否 | 父预留 | 类型约束见对应对象 |
| `estimates` | [ResourceVector](./ResourceVector.md) | 是 | 预留量 | 类型约束见对应对象 |
| `settled_usage_refs` | 数组&lt;[Ref](./Ref.md)&gt; | 是 | 尝试账单 | 最少项 `0`；最多项 `256` |
| `status` | [ReservationState](./ReservationState.md) | 是 | 预留状态 | 类型约束见对应对象 |
| `revision` | [Revision](./Revision.md) | 是 | 账本版本 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
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
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.BudgetReservation`。
