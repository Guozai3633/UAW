# ReplyProposal

状态：对象契约0.2 / conversation-v1；可用范围见具体接口与实施记录。所属：运行与会话。

消息完成候选，无Artifact/VerificationReport或用户接受字段。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `protocol` | 常量 `conversation-v1` | 是 | 协议 | — |
| `run_ref` | [ConversationRunRef](./ConversationRunRef.md) | 是 | 提议结束的原Run版本 | 类型约束见对应对象 |
| `input_revision` | [Revision](./Revision.md) | 是 | 有效原文/补充版本 | ≥ `1`；类型约束见对应对象 |
| `decision_record_ref` | [Ref](./Ref.md) | 是 | 已登记FirstDecisionRecord | 类型约束见对应对象 |
| `text` | [NonEmptyText](./NonEmptyText.md) | 是 | 实际原模型reply文本 | 正则 `\S`；类型约束见对应对象 |
| `source_refs` | 数组&lt;[Ref](./Ref.md)&gt; | 是 | 已实际读取的用户材料/工具引用 | 最少项 `0`；最多项 `32` |
| `unresolved_effect_refs` | 数组&lt;[Ref](./Ref.md)&gt; | 是 | 消息终态依赖未决效果必须为空 | 最少项 `0`；最多项 `0` |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 运行时约束

- 实际commit读取完整Tool/模型账本与当前输入版本，不能只相信提案的空效果列表；来源正文/attempt/模型政策与reply分支必须一致。

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
  "decision_record_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "text": "example_001",
  "source_refs": [],
  "unresolved_effect_refs": []
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.ReplyProposal`。
