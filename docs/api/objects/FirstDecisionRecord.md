# FirstDecisionRecord

状态：对象契约0.2 / conversation-v1；可用范围见具体接口与实施记录。所属：Agent执行与协作。

服务写入的实际模型来源；不能由模型自报。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `protocol` | 常量 `conversation-v1` | 是 | 协议 | — |
| `run_ref` | [ConversationRunRef](./ConversationRunRef.md) | 是 | 原Run版本 | 类型约束见对应对象 |
| `input_revision` | [Revision](./Revision.md) | 是 | 决策使用的输入集合版本 | ≥ `1`；类型约束见对应对象 |
| `decision` | [FirstDecision](./FirstDecision.md) | 是 | 原模型动作 | 类型约束见对应对象 |
| `model_output_ref` | [Ref](./Ref.md) | 是 | Model owning reader固定回执 | 类型约束见对应对象 |
| `model_policy_ref` | [Ref](./Ref.md) | 是 | 原用户固定模型政策 | 类型约束见对应对象 |
| `attempt_id` | [ID](./ID.md) | 是 | 实际ModelOutput尝试，必须与来源一致 | 类型约束见对应对象 |
| `usage_ref` | [Ref](./Ref.md) | 是 | 实际用量，pending保留 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "protocol": "conversation-v1",
  "run_ref": {
    "kind": "run",
    "id": "example_001",
    "version": "example_001"
  },
  "input_revision": 1,
  "decision": {
    "protocol": "conversation-v1",
    "action": "reply",
    "text": "example_001"
  },
  "model_output_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "model_policy_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "attempt_id": "example_001",
  "usage_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  }
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.FirstDecisionRecord`。
