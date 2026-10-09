# AgentRootBinding

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：Agent执行与协作。

内部根实例固定创建来源，不从模型参数取得认证或角色权限。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `context` | [TrustedExecutionContext](./TrustedExecutionContext.md) | 是 | 完整拥有者和执行范围 | 类型约束见对应对象 |
| `start_request` | [AgentStartRequest](./AgentStartRequest.md) | 是 | 原创建参数 | 类型约束见对应对象 |
| `role_ref` | [Ref](./Ref.md) | 是 | 实际角色版本 | 类型约束见对应对象 |
| `max_steps` | [Revision](./Revision.md) | 是 | 有界步数上限 | 类型约束见对应对象 |

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
  "start_request": {
    "run_ref": {
      "kind": "web",
      "id": "example_001",
      "version": "example_001"
    },
    "task_frame_ref": {
      "kind": "web",
      "id": "example_001",
      "version": "example_001"
    },
    "creation_key": "example_001"
  },
  "role_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "max_steps": 0
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.AgentRootBinding`。
