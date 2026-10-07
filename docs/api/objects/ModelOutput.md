# ModelOutput

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：模型调用。

文本与工具建议分别表达。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `attempt_id` | [ID](./ID.md) | 是 | 实际尝试 | 类型约束见对应对象 |
| `actual_config` | [ResolvedModelConfig](./ResolvedModelConfig.md) | 是 | 真实配置 | 类型约束见对应对象 |
| `text` | [Text](./Text.md) | 是 | 可见模型结果 | 类型约束见对应对象 |
| `tool_calls` | 数组&lt;[ToolCall](./ToolCall.md)&gt; | 是 | 拟执行工具；尚未授权 | 最少项 `0`；最多项 `256` |
| `structured_data` | [Object](./Object.md) | 否 | 受output_schema约束的结果 | 类型约束见对应对象 |
| `finish_reason` | [FinishReason](./FinishReason.md) | 是 | 正常/工具/截断等 | 类型约束见对应对象 |
| `usage` | [Usage](./Usage.md) | 是 | 已知用量 | 类型约束见对应对象 |
| `content_ref` | [Ref](./Ref.md) | 否 | 大输出的完整内容引用。 | 类型约束见对应对象 |
| `text_complete` | [Bool](./Bool.md) | 是 | text是否包含本次收到的完整可见文本；不表示整个任务完成。 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## allOf结构规则

```json
{
  "allOf": [
    {
      "if": {
        "properties": {
          "text_complete": {
            "const": false
          }
        },
        "required": [
          "text_complete"
        ]
      },
      "then": {
        "required": [
          "content_ref"
        ]
      }
    }
  ]
}
```

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "attempt_id": "example_001",
  "actual_config": {
    "model_id": "example_001",
    "catalog_revision": 0,
    "provider_ref": {
      "kind": "web",
      "id": "example_001",
      "version": "example_001"
    },
    "policy_ref": {
      "kind": "web",
      "id": "example_001",
      "version": "example_001"
    },
    "max_output_tokens": 0
  },
  "text": "example_001",
  "tool_calls": [],
  "finish_reason": "stop",
  "usage": {
    "attempt_id": "example_001",
    "resources": {
      "model_calls": 0,
      "tool_calls": 0,
      "child_agents": 0,
      "wall_time_ms": 0,
      "currency": "CNY",
      "input_tokens": 0,
      "output_tokens": 0,
      "money": "0"
    },
    "billing_state": "confirmed"
  },
  "text_complete": true
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.ModelOutput`。
