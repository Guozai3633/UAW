# AuditRecord

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：工具运行。

审计只保留脱敏参数摘要和证据引用。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `id` | [ID](./ID.md) | 是 | 记录 | 类型约束见对应对象 |
| `actor` | [Principal](./Principal.md) | 是 | 真实主体 | 类型约束见对应对象 |
| `call_ref` | [Ref](./Ref.md) | 是 | 调用 | 类型约束见对应对象 |
| `approval_ref` | [Ref](./Ref.md) | 否 | 授权依据 | 类型约束见对应对象 |
| `effect_state` | [EffectState](./EffectState.md) | 是 | 真实效果 | 类型约束见对应对象 |
| `usage_ref` | [Ref](./Ref.md) | 是 | 尝试用量 | 类型约束见对应对象 |
| `created_at` | [Timestamp](./Timestamp.md) | 是 | 时间 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "id": "example_001",
  "actor": {
    "id": "example_001",
    "kind": "user",
    "auth_session_id": "example_001"
  },
  "call_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "effect_state": "confirmed",
  "usage_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "created_at": "2026-10-07T02:00:00Z"
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.AuditRecord`。
