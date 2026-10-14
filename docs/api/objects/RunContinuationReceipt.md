# RunContinuationReceipt

状态：对象契约0.2 / conversation-v1；可用范围见具体接口与实施记录。所属：运行与会话。

补充受理和实际生效回执，不等于最终成果完成。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `protocol` | 常量 `conversation-v1` | 是 | 协议 | — |
| `run` | [RunRecord](./RunRecord.md) | 是 | 当前原Run；允许受理后又取消的查询结果 | 类型约束见对应对象 |
| `patch` | [RunInputPatch](./RunInputPatch.md) | 是 | 原请求受理及生效状态 | 类型约束见对应对象 |
| `event_seq` | [Revision](./Revision.md) | 是 | 最后可续持久事件序号 | ≥ `1`；类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "protocol": "conversation-v1",
  "run": {
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
  },
  "patch": {
    "protocol": "conversation-v1",
    "run_id": "example_001",
    "conversation_id": "example_001",
    "request_id": "example_001",
    "input_ref": {
      "kind": "input",
      "id": "example_001",
      "version": "example_001"
    },
    "kind": "clarification_answer",
    "base_input_revision": 1,
    "input_revision": 1,
    "state": "accepted",
    "created_at": "2026-10-07T02:00:00Z",
    "question_item_id": "example_001",
    "question_revision": 1
  },
  "event_seq": 1
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.RunContinuationReceipt`。
