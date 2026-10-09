# AgentObservation

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：Agent执行与协作。

保存真实工具返回和原调用；失败也进入下一轮观察。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `context` | [TrustedExecutionContext](./TrustedExecutionContext.md) | 是 | 完整来源绑定 | 类型约束见对应对象 |
| `call` | [ToolCall](./ToolCall.md) | 是 | 实际调用 | 类型约束见对应对象 |
| `result` | [RuntimeToolruntimeInvokeResult](./RuntimeToolruntimeInvokeResult.md) | 是 | 实际成功等待或失败 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 运行时约束

- 仅可信内部适配器写入，当前拥有者/session/Run/固定模型/角色和资源逐次复查。
- 不证明框架END、模型建议或传输成功已经完成用户任务。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
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
  "call": {
    "tool_ref": {
      "kind": "web",
      "id": "example_001",
      "version": "example_001"
    },
    "arguments": {},
    "action_id": "example_001"
  },
  "result": {
    "kind": "ok",
    "output_refs": [],
    "payload": {
      "call_ref": {
        "kind": "web",
        "id": "example_001",
        "version": "example_001"
      },
      "status": "succeeded",
      "output_refs": [],
      "effect_state": "confirmed",
      "usage_ref": {
        "kind": "web",
        "id": "example_001",
        "version": "example_001"
      }
    }
  }
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.AgentObservation`。
