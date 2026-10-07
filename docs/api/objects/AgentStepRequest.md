# AgentStepRequest

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：Agent执行与协作。

单次推进循环，调度器不越过LLM决策。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `instance_ref` | [Ref](./Ref.md) | 是 | 固定实例 | 类型约束见对应对象 |
| `observations` | 数组&lt;[Ref](./Ref.md)&gt; | 是 | 新增结果 | 最少项 `0`；最多项 `256` |
| `current_frame_ref` | [Ref](./Ref.md) | 是 | 当前理解 | 类型约束见对应对象 |
| `remaining_budget` | [Budget](./Budget.md) | 是 | 可用预算 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "instance_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "observations": [],
  "current_frame_ref": {
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

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.AgentStepRequest`。
