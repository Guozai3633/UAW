# InternalAgentCollaborationChannelRequest

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：Agent执行与协作。

消息与受控引用的私有阶段输入。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `message_id` | [ID](./ID.md) | 是 | 协作消息去重键，重复同内容返回原消息。 | 类型约束见对应对象 |
| `from_ref` | [Ref](./Ref.md) | 是 | 同任务树内真实发送者，由认证上下文核验。 | 类型约束见对应对象 |
| `to_ref` | [Ref](./Ref.md) | 是 | 同任务树获准接收实例，不能越界投递资料。 | 类型约束见对应对象 |
| `payload_refs` | 数组&lt;[Ref](./Ref.md)&gt; | 是 | 允许共享的固定资料/候选结果，不传整个私有上下文。 | 最多项 `256` |
| `task_revision` | [Revision](./Revision.md) | 是 | 协作消息或结果依赖的共同任务修订。 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 运行时约束

- 消息记录归Agent，Run事件仅引用；不共享完整prompt。
- 服务端注入可信上下文，不通过HTTP或LLM工具直接访问。

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
  "payload_refs": [],
  "task_revision": 0
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.InternalAgentCollaborationChannelRequest`。
