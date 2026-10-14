# FirstAskDecision

状态：对象契约0.2 / conversation-v1；可用范围见具体接口与实施记录。所属：Agent执行与协作。

同次首次决策的ask分支，无执行或授权字段。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `protocol` | 常量 `conversation-v1` | 是 | 首次决策版本 | — |
| `understanding` | [ConversationUnderstanding](./ConversationUnderstanding.md) | 否 | 可选同次理解摘要 | 类型约束见对应对象 |
| `action` | 常量 `ask` | 是 | 唯一动作 | — |
| `question` | [ClarificationPrompt](./ClarificationPrompt.md) | 是 | 必要问题 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "protocol": "conversation-v1",
  "action": "ask",
  "question": {
    "text": "example_001",
    "reason": "example_001",
    "options": []
  }
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.FirstAskDecision`。
