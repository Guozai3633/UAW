# RunRecord

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：运行与会话。

调度执行实体；任务历史有多个Run。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `id` | [ID](./ID.md) | 是 | Run | 类型约束见对应对象 |
| `task_id` | [ID](./ID.md) | 是 | 任务 | 类型约束见对应对象 |
| `conversation_id` | [ID](./ID.md) | 是 | 入口会话 | 类型约束见对应对象 |
| `revision` | [Revision](./Revision.md) | 是 | 状态版本 | 类型约束见对应对象 |
| `status` | [RunStatus](./RunStatus.md) | 是 | 当前状态 | 类型约束见对应对象 |
| `root_agent_ref` | [Ref](./Ref.md) | 否 | 根实例 | 类型约束见对应对象 |
| `frame_ref` | [Ref](./Ref.md) | 否 | 当前任务理解 | 类型约束见对应对象 |
| `plan_ref` | [Ref](./Ref.md) | 否 | 可选图 | 类型约束见对应对象 |
| `budget` | [Budget](./Budget.md) | 是 | 上限 | 类型约束见对应对象 |
| `outcome` | [Outcome](./Outcome.md) | 否 | 终态 | 类型约束见对应对象 |
| `created_at` | [Timestamp](./Timestamp.md) | 是 | 受理时间 | 类型约束见对应对象 |
| `ended_at` | [Timestamp](./Timestamp.md) | 否 | 实际结束 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
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
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.RunRecord`。
