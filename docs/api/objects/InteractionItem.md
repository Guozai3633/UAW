# InteractionItem

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：运行与会话。

稳定前端交互对象，不依赖猜模型文本。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `id` | [ID](./ID.md) | 是 | 交互项 | 类型约束见对应对象 |
| `conversation_id` | [ID](./ID.md) | 是 | 会话 | 类型约束见对应对象 |
| `run_id` | [ID](./ID.md) | 否 | 运行 | 类型约束见对应对象 |
| `type` | [ItemType](./ItemType.md) | 是 | 消息/工具/文件/审批等 | 类型约束见对应对象 |
| `status` | [ItemStatus](./ItemStatus.md) | 是 | 交互状态 | 类型约束见对应对象 |
| `revision` | [Revision](./Revision.md) | 是 | 项版本 | 类型约束见对应对象 |
| `text` | [Text](./Text.md) | 是 | 可见内容 | 类型约束见对应对象 |
| `resource_refs` | 数组&lt;[Ref](./Ref.md)&gt; | 是 | 关联真实资源 | 最少项 `0`；最多项 `256` |
| `created_at` | [Timestamp](./Timestamp.md) | 是 | 开始 | 类型约束见对应对象 |
| `updated_at` | [Timestamp](./Timestamp.md) | 是 | 最近更新 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "id": "example_001",
  "conversation_id": "example_001",
  "type": "user_message",
  "status": "pending",
  "revision": 0,
  "text": "example_001",
  "resource_refs": [],
  "created_at": "2026-10-07T02:00:00Z",
  "updated_at": "2026-10-07T02:00:00Z"
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.InteractionItem`。
