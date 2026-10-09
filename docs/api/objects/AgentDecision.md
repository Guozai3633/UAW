# AgentDecision

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：Agent执行与协作。

固定模型的有界建议，无完成或执行授权。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `action` | [AgentStepAction](./AgentStepAction.md) | 是 | 拟采取动作 | 类型约束见对应对象 |
| `text` | [Text](./Text.md) | 是 | 答复或解释 | 最多字符 `16384`；类型约束见对应对象 |
| `proposed_calls` | 数组&lt;[ToolCall](./ToolCall.md)&gt; | 是 | 至多一个待授权工具 | 最少项 `0`；最多项 `1` |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "action": "respond",
  "text": "example_001",
  "proposed_calls": []
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.AgentDecision`。
