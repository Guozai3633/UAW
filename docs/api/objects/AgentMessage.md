# AgentMessage

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：Agent执行与协作。

协作通道只传授权引用和短消息。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `message_id` | [ID](./ID.md) | 是 | 通道去重键 | 类型约束见对应对象 |
| `from_ref` | [Ref](./Ref.md) | 是 | 发送实例 | 类型约束见对应对象 |
| `to_ref` | [Ref](./Ref.md) | 是 | 接收实例 | 类型约束见对应对象 |
| `task_revision` | [Revision](./Revision.md) | 是 | 共同任务基线 | 类型约束见对应对象 |
| `text` | [Text](./Text.md) | 是 | 协作内容 | 类型约束见对应对象 |
| `payload_refs` | 数组&lt;[Ref](./Ref.md)&gt; | 是 | 共享资料/候选结果 | 最少项 `0`；最多项 `256` |
| `created_at` | [Timestamp](./Timestamp.md) | 是 | 提交时间 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "message_id": "example_001",
  "from_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "to_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "task_revision": 0,
  "text": "example_001",
  "payload_refs": [],
  "created_at": "2026-10-07T02:00:00Z"
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.AgentMessage`。
