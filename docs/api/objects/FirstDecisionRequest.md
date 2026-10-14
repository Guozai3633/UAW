# FirstDecisionRequest

状态：对象契约0.2 / conversation-v1；可用范围见具体接口与实施记录。所属：Agent执行与协作。

首次调用不要求独立TaskFrame；Context仅最小必要来源。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `protocol` | 常量 `conversation-v1` | 是 | 协议 | — |
| `run_ref` | [ConversationRunRef](./ConversationRunRef.md) | 是 | 原Run版本 | 类型约束见对应对象 |
| `original_input_ref` | [UserInputRef](./UserInputRef.md) | 是 | 原文来源 | 类型约束见对应对象 |
| `patch_refs` | 数组&lt;[UserInputRef](./UserInputRef.md)&gt; | 是 | 已受理的有效补充 | 最少项 `0`；最多项 `32`；去重 `True` |
| `input_revision` | [Revision](./Revision.md) | 是 | 输入集合版本 | ≥ `1`；类型约束见对应对象 |
| `context_ref` | [Ref](./Ref.md) | 是 | 有界ContextSnapshot | 类型约束见对应对象 |
| `remaining_budget` | [Budget](./Budget.md) | 是 | 本次有效调用预算，不复制原完整时限 | 类型约束见对应对象 |

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
  "original_input_ref": {
    "kind": "input",
    "id": "example_001",
    "version": "example_001"
  },
  "patch_refs": [],
  "input_revision": 1,
  "context_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "remaining_budget": {
    "limits": {
      "input_tokens": 0,
      "output_tokens": 0,
      "model_calls": 0,
      "tool_calls": 0,
      "child_agents": 0,
      "wall_time_ms": 0,
      "money": "0",
      "currency": "CNY"
    },
    "max_steps": 0,
    "max_depth": 0,
    "deadline": "2026-10-07T02:00:00Z"
  }
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.FirstDecisionRequest`。
