# ClarificationProposal

状态：对象契约0.2 / conversation-v1；可用范围见具体接口与实施记录。所属：运行与会话。

服务从实际ask动作创建的问题提交候选，不是用户授权。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `protocol` | 常量 `conversation-v1` | 是 | 协议 | — |
| `run_ref` | [ConversationRunRef](./ConversationRunRef.md) | 是 | 原Run预期版本 | 类型约束见对应对象 |
| `input_revision` | [Revision](./Revision.md) | 是 | 原有效输入版本 | ≥ `1`；类型约束见对应对象 |
| `decision_record_ref` | [Ref](./Ref.md) | 是 | 服务登记的原ask模型回执 | 类型约束见对应对象 |
| `prompt` | [ClarificationPrompt](./ClarificationPrompt.md) | 是 | 须与实际ask输出一致 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 运行时约束

- Run复查原ask/当前版本/取消/在途调用；问题Item、等待、时钟和事件同域提交；存在在途调用不能暂停主动计时。

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
  "prompt": {
    "text": "example_001",
    "reason": "example_001",
    "options": []
  }
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.ClarificationProposal`。
