# BudgetAttemptState

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：运行与会话。

预算owning-domain当前实际意图/期限，查询不授权发送。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `run_id` | [ID](./ID.md) | 是 | 运行 | 类型约束见对应对象 |
| `operation_id` | [ID](./ID.md) | 是 | 原操作 | 类型约束见对应对象 |
| `trace_id` | [ID](./ID.md) | 是 | 原trace | 类型约束见对应对象 |
| `attempt_id` | [ID](./ID.md) | 是 | 原尝试 | 类型约束见对应对象 |
| `reservation_ref` | [Ref](./Ref.md) | 是 | 当前预留版本 | 类型约束见对应对象 |
| `deadline` | [Timestamp](./Timestamp.md) | 是 | 实际尝试期限 | 类型约束见对应对象 |
| `dispatched` | [Bool](./Bool.md) | 是 | 已保存预算dispatch意图 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
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
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.BudgetAttemptState`。
