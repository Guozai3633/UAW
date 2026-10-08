# RunnerAuthoritySnapshot

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：工作区与交付。

可信异步通道及服务记录解析的当前执行权威；没有本机路径或自报批准字段。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `context` | [TrustedExecutionContext](./TrustedExecutionContext.md) | 是 | 实际授权上下文 | 类型约束见对应对象 |
| `device_id` | [ID](./ID.md) | 是 | 当前设备 | 类型约束见对应对象 |
| `root_handle` | [ID](./ID.md) | 是 | 实际授权根 | 类型约束见对应对象 |
| `workspace_ref` | [Ref](./Ref.md) | 是 | 工作区版本 | 类型约束见对应对象 |
| `binding_revision` | [Revision](./Revision.md) | 是 | 根绑定版本 | 类型约束见对应对象 |
| `fencing_token` | [Revision](./Revision.md) | 是 | 当前栅栏 | 类型约束见对应对象 |
| `lease_expires_at` | [Timestamp](./Timestamp.md) | 是 | 当前租约期限 | 类型约束见对应对象 |
| `request_ref` | [Ref](./Ref.md) | 是 | 存储业务请求 | 类型约束见对应对象 |
| `request_parameters` | [RunnerParameters](./RunnerParameters.md) | 是 | 存储业务参数 | 类型约束见对应对象 |
| `policy_ref` | [Ref](./Ref.md) | 是 | 当前政策 | 类型约束见对应对象 |
| `required_scope_capability` | [NonEmptyText](./NonEmptyText.md) | 是 | 需要的能力 | 类型约束见对应对象 |
| `allowed_actions` | 数组&lt;[ID](./ID.md)&gt; | 是 | 当前获准动作 | 最少项 `0`；最多项 `256` |
| `feature_enabled` | [Bool](./Bool.md) | 是 | 实际开关 | 类型约束见对应对象 |
| `connected` | [Bool](./Bool.md) | 是 | 实际连接 | 类型约束见对应对象 |
| `cancelled` | [Bool](./Bool.md) | 是 | 当前取消状态 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 运行时约束

- 来源必须是认证通道和拥有者存储，command.trusted_context仅供对比，不能作为权威来源。
- snapshot不允许缓存后执行；所有字段必需，无默认批准/无限期限；没有真实authority或IPC时不可用。

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
  "device_id": "example_001",
  "root_handle": "example_001",
  "workspace_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "binding_revision": 0,
  "fencing_token": 0,
  "lease_expires_at": "2026-10-07T02:00:00Z",
  "request_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "request_parameters": {
    "action": "workspace.capture",
    "parameters": {
      "source_ref": {
        "kind": "web",
        "id": "example_001",
        "version": "example_001"
      },
      "base_kind": "commit",
      "include_rules": {
        "include_uncommitted": true,
        "include_untracked": true,
        "include_paths": [],
        "exclude_paths": [],
        "max_total_bytes": 0
      },
      "expected_source_revision": "example_001"
    }
  },
  "policy_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "required_scope_capability": "example_001",
  "allowed_actions": [],
  "feature_enabled": true,
  "connected": true,
  "cancelled": true
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.RunnerAuthoritySnapshot`。
