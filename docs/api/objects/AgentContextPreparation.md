# AgentContextPreparation

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：Agent执行与协作。

原步骤的上下文登记意图；恢复保持原配方CAS参数。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `context` | [TrustedExecutionContext](./TrustedExecutionContext.md) | 是 | 原步骤上下文 | 类型约束见对应对象 |
| `request` | [ContextRequest](./ContextRequest.md) | 是 | 固定配方参数 | 类型约束见对应对象 |
| `rules` | [InternalContextRulesRequest](./InternalContextRulesRequest.md) | 是 | 固定规则选择 | 类型约束见对应对象 |
| `tools` | [ModelToolSet](./ModelToolSet.md) | 是 | 真实工具集合 | 类型约束见对应对象 |
| `revision` | [Revision](./Revision.md) | 是 | CAS | 类型约束见对应对象 |
| `snapshot_ref` | [Ref](./Ref.md) | 否 | 实际构建后快照 | 类型约束见对应对象 |

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
    "purpose": "draft_preview",
    "source_refs": [],
    "model_policy_ref": {
      "kind": "web",
      "id": "example_001",
      "version": "example_001"
    },
    "output_reserve": 0,
    "tool_reserve": 0,
    "preserve": {
      "required_refs": [],
      "exact_strings": [],
      "requirement_ids": [],
      "pending_action_refs": []
    },
    "expected_epoch": 0
  },
  "rules": {
    "scope_paths": [],
    "user_instruction_refs": [],
    "activated_skill_refs": []
  },
  "tools": {
    "run_id": "example_001",
    "tools": []
  },
  "revision": 0
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.AgentContextPreparation`。
