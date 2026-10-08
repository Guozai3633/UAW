# RunnerRequestRecord

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：运行与会话。

版本1的原请求/原尝试，不是执行权限。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `id` | [ID](./ID.md) | 是 | 稳定请求 | 类型约束见对应对象 |
| `context` | [TrustedExecutionContext](./TrustedExecutionContext.md) | 是 | 服务取得的原上下文 | 类型约束见对应对象 |
| `parameters` | [RunnerParameters](./RunnerParameters.md) | 是 | 原业务参数 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "id": "example_001",
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
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.RunnerRequestRecord`。
