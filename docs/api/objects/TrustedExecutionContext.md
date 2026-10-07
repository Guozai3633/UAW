# TrustedExecutionContext

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：公共协议。

服务端/Runner注入，不属于模型/HTTP请求体。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `principal` | [Principal](./Principal.md) | 是 | 可信主体 | 类型约束见对应对象 |
| `scope` | [Scope](./Scope.md) | 是 | 当前有效范围 | 类型约束见对应对象 |
| `operation_id` | [ID](./ID.md) | 是 | 操作关联 | 类型约束见对应对象 |
| `conversation_id` | [ID](./ID.md) | 否 | 会话 | 类型约束见对应对象 |
| `task_id` | [ID](./ID.md) | 否 | 任务 | 类型约束见对应对象 |
| `run_id` | [ID](./ID.md) | 否 | Run；正式执行必需 | 类型约束见对应对象 |
| `agent_id` | [ID](./ID.md) | 否 | 实例 | 类型约束见对应对象 |
| `node_id` | [ID](./ID.md) | 否 | 节点 | 类型约束见对应对象 |
| `trace_id` | [ID](./ID.md) | 是 | 诊断关联 | 类型约束见对应对象 |
| `attempt_id` | [ID](./ID.md) | 是 | 执行尝试 | 类型约束见对应对象 |
| `deadline` | [Timestamp](./Timestamp.md) | 是 | 剩余时间据此计算 | 类型约束见对应对象 |
| `model_policy_ref` | [Ref](./Ref.md) | 否 | 有效模型政策 | 类型约束见对应对象 |
| `capability_policy_ref` | [Ref](./Ref.md) | 是 | 有效能力政策 | 类型约束见对应对象 |
| `budget_reservation_ref` | [Ref](./Ref.md) | 否 | 已预留预算 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
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
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.TrustedExecutionContext`。
