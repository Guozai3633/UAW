# InternalRunResumeOutputResume

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：运行与会话。

按action选择的独立参数/结果分支。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `action` | 常量 `resume` | 是 | 分支标识 | — |
| `result` | [RunRecord](./RunRecord.md) | 是 | 该分支的明确结构 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "action": "resume",
  "result": {
    "id": "example_001",
    "task_id": "example_001",
    "conversation_id": "example_001",
    "revision": 0,
    "status": "queued",
    "budget": {
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
    },
    "created_at": "2026-10-07T02:00:00Z"
  }
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.InternalRunResumeOutputResume`。
