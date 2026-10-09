# AgentLoopOperation

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：Agent执行与协作。

原步骤及原模型/工具尝试，恢复不换ID重新发送。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `id` | [ID](./ID.md) | 是 | 操作 | 类型约束见对应对象 |
| `instance_id` | [ID](./ID.md) | 是 | 根实例 | 类型约束见对应对象 |
| `revision` | [Revision](./Revision.md) | 是 | CAS | 类型约束见对应对象 |
| `step` | [Revision](./Revision.md) | 是 | 步数 | 类型约束见对应对象 |
| `request` | [AgentStepRequest](./AgentStepRequest.md) | 是 | 固定请求 | 类型约束见对应对象 |
| `context` | [TrustedExecutionContext](./TrustedExecutionContext.md) | 是 | 原模型尝试 | 类型约束见对应对象 |
| `phase` | [AgentOperationPhase](./AgentOperationPhase.md) | 是 | 持久阶段 | 类型约束见对应对象 |
| `snapshot_ref` | [Ref](./Ref.md) | 否 | 实际上下文快照 | 类型约束见对应对象 |
| `context_epoch` | [Revision](./Revision.md) | 否 | 实际快照纪元，不是模型步数 | 类型约束见对应对象 |
| `model_request` | [ModelCall](./ModelCall.md) | 否 | 原模型调用 | 类型约束见对应对象 |
| `model_result` | [RuntimeModelruntimeGenerateResult](./RuntimeModelruntimeGenerateResult.md) | 否 | 实际模型回执 | 类型约束见对应对象 |
| `proposal` | [AgentDecision](./AgentDecision.md) | 否 | 已验证建议 | 类型约束见对应对象 |
| `tool_context` | [TrustedExecutionContext](./TrustedExecutionContext.md) | 否 | 原工具尝试 | 类型约束见对应对象 |
| `observation_ref` | [Ref](./Ref.md) | 否 | 登记结果 | 类型约束见对应对象 |
| `result` | [RuntimeAgentruntimeStepResult](./RuntimeAgentruntimeStepResult.md) | 否 | 实际步骤结果 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 运行时约束

- 仅可信内部适配器写入，当前拥有者/session/Run/固定模型/角色和资源逐次复查。
- 不证明框架END、模型建议或传输成功已经完成用户任务。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "id": "example_001",
  "instance_id": "example_001",
  "revision": 0,
  "step": 0,
  "request": {
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
  },
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
  "phase": "claimed"
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.AgentLoopOperation`。
