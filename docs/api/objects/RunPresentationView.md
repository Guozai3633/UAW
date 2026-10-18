# RunPresentationView

状态：对象契约0.2 / conversation-v1；可用范围见具体接口与实施记录。所属：运行与会话。

同一只读数据库快照中的显示阶段、真实理解及当前成果；不授权执行或完成。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `protocol` | 常量 `conversation-v1` | 是 | 协议 | — |
| `run` | [RunRecord](./RunRecord.md) | 是 | 权威原Run，保持原CAS修订和状态 | 类型约束见对应对象 |
| `input_revision` | [Revision](./Revision.md) | 是 | 当前有效输入版本 | ≥ `1`；类型约束见对应对象 |
| `phase` | enum: `preparing` / `working` / `verifying` / `waiting_for_user` / `awaiting_acceptance` / `finalizing` / `needs_revision` / `stopping` / `completed` / `failed` / `cancelled` / `unavailable` | 是 | 显示阶段，不替代Run.status；取消受理尚未终态为stopping | — |
| `understanding` | [RunPresentationUnderstanding](./RunPresentationUnderstanding.md) | 是 | 真实理解状态与来源 | 类型约束见对应对象 |
| `delivery` | [RunPresentationDelivery](./RunPresentationDelivery.md) | 否 | 仅返回同一当前Run修订和输入的成果 | 类型约束见对应对象 |
| `stopped_reply_ref` | [Ref](./Ref.md) | 否 | 原普通回复与调用已停止的证据；仅释放本地发送查询，不结算Run/费用或授权续跑 | 类型约束见对应对象 |
| `captured_at` | [Timestamp](./Timestamp.md) | 是 | 一致性快照读取时间 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 运行时约束

- 读取原Run、输入、实际决策/ModelOutput、原job及当前成果；同一次REPEATABLE READ READ ONLY事务，不写事件或执行。
- awaiting_acceptance要求当前完整成果、实际交付等待、原合同要求接受、核验成功且未接受；旧成果或unknown不得推断完成。
- 已有Frame、Proposal和Run不因显示理解/阶段被改写；缺源503/明确不可用；0.1与旧conversation端点不变。

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
  "phase": "preparing",
  "understanding": {
    "state": "pending",
    "input_revision": 1
  },
  "captured_at": "2026-10-07T02:00:00Z"
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.RunPresentationView`。
