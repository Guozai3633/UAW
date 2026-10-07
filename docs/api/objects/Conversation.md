# Conversation

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：运行与会话。

会话不等于Task；首期单用户仍有独立主体。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `id` | [ID](./ID.md) | 是 | 会话 | 类型约束见对应对象 |
| `owner_id` | [ID](./ID.md) | 是 | 服务注入用户 | 类型约束见对应对象 |
| `title` | [NonEmptyText](./NonEmptyText.md) | 是 | 标题 | 类型约束见对应对象 |
| `revision` | [Revision](./Revision.md) | 是 | 会话版本 | 类型约束见对应对象 |
| `project_ref` | [Ref](./Ref.md) | 否 | 可选本地/云项目绑定 | 类型约束见对应对象 |
| `model_policy_ref` | [Ref](./Ref.md) | 是 | 会话模型选择 | 类型约束见对应对象 |
| `memory_policy` | [MemoryPolicy](./MemoryPolicy.md) | 是 | 独立读写开关 | 类型约束见对应对象 |
| `created_at` | [Timestamp](./Timestamp.md) | 是 | 创建时间 | 类型约束见对应对象 |
| `updated_at` | [Timestamp](./Timestamp.md) | 是 | 修改时间 | 类型约束见对应对象 |
| `approval_mode` | [ApprovalMode](./ApprovalMode.md) | 是 | 用户选择；不能扩大管理员政策与本机权限。 | 默认注解 `manual`；类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "id": "example_001",
  "owner_id": "example_001",
  "title": "example_001",
  "revision": 0,
  "model_policy_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "memory_policy": {
    "revision": 0,
    "read_enabled": true,
    "contribute_enabled": true,
    "scope": {
      "conversation_id": "example_001"
    }
  },
  "created_at": "2026-10-07T02:00:00Z",
  "updated_at": "2026-10-07T02:00:00Z",
  "approval_mode": "assisted"
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.Conversation`。
