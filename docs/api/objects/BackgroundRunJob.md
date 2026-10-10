# BackgroundRunJob

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：运行与会话。

内部有界持久单Agent任务；claim栅栏不替代执行权限，恢复原attempt。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `run_id` | [ID](./ID.md) | 是 | 原Run | 类型约束见对应对象 |
| `principal` | [Principal](./Principal.md) | 是 | 原认证用户会话 | 类型约束见对应对象 |
| `revision` | [Revision](./Revision.md) | 是 | 持久CAS | 类型约束见对应对象 |
| `fence` | [Revision](./Revision.md) | 是 | 单调worker栅栏 | 类型约束见对应对象 |
| `state` | enum: `queued` / `working` / `waiting` / `blocked` / `finished` | 是 | 调度状态 | — |
| `stage` | enum: `admitted` / `prepared` / `understood` / `started` / `step` / `delivery` / `finished` | 是 | 原执行阶段 | — |
| `step` | integer | 是 | 原步骤序号 | ≥ `0`；≤ `64` |
| `ready_at` | [Timestamp](./Timestamp.md) | 是 | 下次检查时间 | 类型约束见对应对象 |
| `worker_id` | [ID](./ID.md) | 否 | 当前进程holder | 类型约束见对应对象 |
| `lease_expires` | [Timestamp](./Timestamp.md) | 否 | holder期限 | 类型约束见对应对象 |
| `context` | [TrustedExecutionContext](./TrustedExecutionContext.md) | 否 | 实际Run/模型/政策绑定 | 类型约束见对应对象 |
| `frame_ref` | [Ref](./Ref.md) | 否 | 实际理解版本 | 类型约束见对应对象 |
| `role_ref` | [Ref](./Ref.md) | 否 | 实际根角色 | 类型约束见对应对象 |
| `instance_ref` | [Ref](./Ref.md) | 否 | 原根实例 | 类型约束见对应对象 |
| `step_context` | [TrustedExecutionContext](./TrustedExecutionContext.md) | 否 | 原步骤attempt/operation，不以新调用替代 | 类型约束见对应对象 |
| `proposal_ref` | [Ref](./Ref.md) | 否 | 实际完成提案 | 类型约束见对应对象 |
| `failure` | [Failure](./Failure.md) | 否 | 保留失败或未知效果 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "run_id": "example_001",
  "principal": {
    "id": "example_001",
    "kind": "user",
    "auth_session_id": "example_001"
  },
  "revision": 0,
  "fence": 0,
  "state": "queued",
  "stage": "admitted",
  "step": 0,
  "ready_at": "2026-10-07T02:00:00Z"
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.BackgroundRunJob`。
