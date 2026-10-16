# RunConversationView

状态：对象契约0.2 / conversation-v1；可用范围见具体接口与实施记录。所属：运行与会话。

当前Run对话控制读图；问题ID来自持久来源，不猜消息文本。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `protocol` | 常量 `conversation-v1` | 是 | 对话协议 | — |
| `run` | [RunRecord](./RunRecord.md) | 是 | 当前原Run及CAS修订 | 类型约束见对应对象 |
| `input_revision` | [Revision](./Revision.md) | 是 | 当前有效输入版本 | ≥ `1`；类型约束见对应对象 |
| `question` | [ClarificationView](./ClarificationView.md) | 否 | 当前仍开放的具体问题；没有时省略，不传null | 类型约束见对应对象 |
| `continuation_request_ids` | 数组&lt;[ID](./ID.md)&gt; | 是 | 按输入版本排序的既有补充request_id；查询原回执用 | 最少项 `0`；最多项 `64`；去重 `True` |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 运行时约束

- 同一事务内读取当前owned会话/Run/协议/输入集/问题/补充；问题必须与当前Run/input版本一致。
- 只读，不触发执行/续期/重发；旧Run无协议返回明确503，取消/终态保持可读。
- question只在open且原Run等待时返回；人工工具审批与成果接受不伪装成澄清。

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
  "input_revision": 1,
  "continuation_request_ids": []
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.RunConversationView`。
