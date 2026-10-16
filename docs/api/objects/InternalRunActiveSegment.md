# InternalRunActiveSegment

状态：对象契约0.2 / conversation-v1；可用范围见具体接口与实施记录。所属：运行与会话。

可信服务在原事务签发的新执行段；非HTTP或模型输入。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `protocol` | 常量 `conversation-v1` | 是 | 协议 | — |
| `run_id` | [ID](./ID.md) | 是 | 原Run | 类型约束见对应对象 |
| `revision` | [Revision](./Revision.md) | 是 | 执行段CAS修订 | ≥ `1`；类型约束见对应对象 |
| `input_revision` | [Revision](./Revision.md) | 是 | 签发时的有效补充版本 | ≥ `1`；类型约束见对应对象 |
| `context` | [TrustedExecutionContext](./TrustedExecutionContext.md) | 是 | 仅新调用使用的新上下文；旧上下文保留 | 类型约束见对应对象 |
| `source_job_ref` | [Ref](./Ref.md) | 是 | 原blocked作业历史版本和完整摘要 | 类型约束见对应对象 |
| `clock_ref` | [ConversationClockRef](./ConversationClockRef.md) | 是 | 实际active时钟历史版本和摘要 | 类型约束见对应对象 |
| `budget_hash` | [Hash](./Hash.md) | 是 | 原Run预算全量摘要，不增加资源或限额 | 类型约束见对应对象 |
| `ledger_deadline` | [Timestamp](./Timestamp.md) | 是 | 原账本截止时间，不能改写 | 类型约束见对应对象 |
| `issued_at` | [Timestamp](./Timestamp.md) | 是 | 原active时钟捕获时刻 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 运行时约束

- 只在同Run安全续跑事务中由实际D时钟剩余额度派生，源作业与时钟历史必须可复核。
- 不修改旧Run预算/账本deadline、invocation、预留、审批或native授权；新段不是权限或额度扩张。
- 缺生产clock/源版本、归属变化、取消、时钟停止或原额度耗尽均拒绝；旧协议原期限不变。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "protocol": "conversation-v1",
  "run_id": "example_001",
  "revision": 1,
  "input_revision": 1,
  "context": {
    "principal": {
      "id": "example_001",
      "kind": "user",
      "auth_session_id": "example_001"
    },
    "scope": {
      "principal_id": "example_001"
    },
    "operation_id": "example_001",
    "trace_id": "example_001",
    "attempt_id": "example_001",
    "deadline": "2026-10-07T02:00:00Z",
    "capability_policy_ref": {
      "kind": "web",
      "id": "example_001",
      "version": "example_001"
    }
  },
  "source_job_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "clock_ref": {
    "kind": "checkpoint",
    "id": "example_001",
    "version": "example_001"
  },
  "budget_hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "ledger_deadline": "2026-10-07T02:00:00Z",
  "issued_at": "2026-10-07T02:00:00Z"
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.InternalRunActiveSegment`。
