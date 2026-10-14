# ConversationProtocolBinding

状态：对象契约0.2 / conversation-v1；可用范围见具体接口与实施记录。所属：运行与会话。

新Run专用版本绑定；不转换旧Run或改写旧Budget语义。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `protocol` | 常量 `conversation-v1` | 是 | 实际准入的版本 | — |
| `run_id` | [ID](./ID.md) | 是 | 新Run | 类型约束见对应对象 |
| `owner_id` | [ID](./ID.md) | 是 | 服务从原会话核实的用户 | 类型约束见对应对象 |
| `revision` | [Revision](./Revision.md) | 是 | 绑定CAS修订 | ≥ `1`；类型约束见对应对象 |
| `input_revision` | [Revision](./Revision.md) | 是 | 当前有效输入集合版本 | ≥ `1`；类型约束见对应对象 |
| `completion_mode` | enum: `message` / `delivery` | 是 | 消息或正式交付 | — |
| `clock_ref` | [ConversationClockRef](./ConversationClockRef.md) | 是 | 新Run专属计时检查点 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 运行时约束

- 只有服务准入记录可启用新模式；缺记录使用legacy固定原deadline；不能从模型参数推断绑定。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "protocol": "conversation-v1",
  "run_id": "example_001",
  "owner_id": "example_001",
  "revision": 1,
  "input_revision": 1,
  "completion_mode": "message",
  "clock_ref": {
    "kind": "checkpoint",
    "id": "example_001",
    "version": "example_001"
  }
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.ConversationProtocolBinding`。
