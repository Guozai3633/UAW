# AttemptTrace

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：配置与共享基础设施。

脱敏运行观测，不保存输入正文、认证头或秘密。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `operation_id` | [ID](./ID.md) | 是 | 操作 | 类型约束见对应对象 |
| `trace_id` | [ID](./ID.md) | 是 | 链路 | 类型约束见对应对象 |
| `attempt_id` | [ID](./ID.md) | 是 | 尝试 | 类型约束见对应对象 |
| `run_id` | [ID](./ID.md) | 是 | 运行 | 类型约束见对应对象 |
| `reservation_ref` | [Ref](./Ref.md) | 是 | 额度 | 类型约束见对应对象 |
| `status` | [NonEmptyText](./NonEmptyText.md) | 是 | 实际结果 | 类型约束见对应对象 |
| `usage_ref` | [Ref](./Ref.md) | 是 | 实际用量 | 类型约束见对应对象 |
| `created_at` | [Timestamp](./Timestamp.md) | 是 | 记录时间 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "operation_id": "example_001",
  "trace_id": "example_001",
  "attempt_id": "example_001",
  "run_id": "example_001",
  "reservation_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "status": "example_001",
  "usage_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "created_at": "2026-10-07T02:00:00Z"
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.AttemptTrace`。
