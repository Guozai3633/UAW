# EventEnvelope

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：运行与会话。

持久事件有序号、版本与可追溯项。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `event_id` | [ID](./ID.md) | 是 | 事件去重键 | 类型约束见对应对象 |
| `stream_id` | [ID](./ID.md) | 是 | 作用域流 | 类型约束见对应对象 |
| `seq` | [Revision](./Revision.md) | 是 | 单调流序号 | 类型约束见对应对象 |
| `type` | [EventType](./EventType.md) | 是 | 注册事件类型；payload_ref解引用后按EventPayload分支校验。 | 类型约束见对应对象 |
| `schema_version` | [Version](./Version.md) | 是 | 事件协议版本 | 类型约束见对应对象 |
| `occurred_at` | [Timestamp](./Timestamp.md) | 是 | 提交时间 | 类型约束见对应对象 |
| `item_ref` | [Ref](./Ref.md) | 否 | 交互项 | 类型约束见对应对象 |
| `payload_ref` | [Ref](./Ref.md) | 是 | 固定类型的事件payload | 类型约束见对应对象 |
| `base_revision` | [Revision](./Revision.md) | 否 | 应用前版本 | 类型约束见对应对象 |
| `result_revision` | [Revision](./Revision.md) | 否 | 应用后版本 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "event_id": "example_001",
  "stream_id": "example_001",
  "seq": 0,
  "type": "input.committed",
  "schema_version": "example_001",
  "occurred_at": "2026-10-07T02:00:00Z",
  "payload_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  }
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.EventEnvelope`。
