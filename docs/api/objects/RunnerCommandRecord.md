# RunnerCommandRecord

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：运行与会话。

已签名不可变命令及登记来源；状态撤销不覆盖签字正文。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `command` | [RunnerCommand](./RunnerCommand.md) | 是 | 实际签字正文 | 类型约束见对应对象 |
| `device_ref` | [Ref](./Ref.md) | 是 | 固定设备绑定 | 类型约束见对应对象 |
| `lease_ref` | [Ref](./Ref.md) | 是 | 固定租约 | 类型约束见对应对象 |
| `holder` | [Principal](./Principal.md) | 是 | 真实执行服务 | 类型约束见对应对象 |
| `root` | [RunnerRootSnapshot](./RunnerRootSnapshot.md) | 是 | 实际根来源 | 类型约束见对应对象 |
| `revision` | [Revision](./Revision.md) | 是 | 登记状态CAS | 类型约束见对应对象 |
| `state` | [RunnerCommandState](./RunnerCommandState.md) | 是 | 是否允许新准入 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "command": {
    "command_id": "example_001",
    "operation_id": "example_001",
    "request_ref": {
      "kind": "web",
      "id": "example_001",
      "version": "example_001"
    },
    "trusted_context": {
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
    "fencing_token": 0,
    "expires_at": "2026-10-07T02:00:00Z",
    "signature": "example_001",
    "parameters": {
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
    }
  },
  "device_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "lease_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "holder": {
    "id": "example_001",
    "kind": "user",
    "auth_session_id": "example_001"
  },
  "root": {
    "owner": {
      "id": "example_001",
      "kind": "user",
      "auth_session_id": "example_001"
    },
    "device_id": "example_001",
    "workspace_ref": {
      "kind": "web",
      "id": "example_001",
      "version": "example_001"
    },
    "root_handle": "example_001",
    "binding_revision": 0,
    "allowed_actions": [],
    "expires_at": "2026-10-07T02:00:00Z"
  },
  "revision": 0,
  "state": "active"
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.RunnerCommandRecord`。
