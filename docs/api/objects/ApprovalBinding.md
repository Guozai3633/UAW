# ApprovalBinding

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：运行与会话。

审批内部权威绑定；只由Run/获准Tool适配器构造，不接受模型或HTTP提供可信上下文。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `context` | [TrustedExecutionContext](./TrustedExecutionContext.md) | 是 | 固定主体、Run、动作上下文 | 类型约束见对应对象 |
| `request` | [ApprovalCreateRequest](./ApprovalCreateRequest.md) | 是 | 固定动作参数摘要、资源和效果 | 类型约束见对应对象 |
| `configuration_ref` | [Ref](./Ref.md) | 是 | Run受理配置 | 类型约束见对应对象 |
| `approval_policy_ref` | [Ref](./Ref.md) | 是 | 固定审批政策 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

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
  "request": {
    "action_id": "example_001",
    "arguments_hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
    "resource_refs": [],
    "effect": "read",
    "summary": "example_001",
    "expires_at": "2026-10-07T02:00:00Z"
  },
  "configuration_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "approval_policy_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  }
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.ApprovalBinding`。
