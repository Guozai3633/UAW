# CompletionBundle

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：Agent执行与协作。

不可变成果、合同、报告和完成提案的版本关联。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `id` | [ID](./ID.md) | 是 | 原Agent操作派生身份 | 类型约束见对应对象 |
| `context` | [TrustedExecutionContext](./TrustedExecutionContext.md) | 是 | 可信完整运行关联 | 类型约束见对应对象 |
| `instance_id` | [ID](./ID.md) | 是 | 原Agent实例 | 类型约束见对应对象 |
| `frame_ref` | [Ref](./Ref.md) | 是 | 实际TaskFrame | 类型约束见对应对象 |
| `contract_ref` | [Ref](./Ref.md) | 是 | 原文、约束和输出要求形成的合同 | 类型约束见对应对象 |
| `artifact_ref` | [Ref](./Ref.md) | 是 | 实际成果 | 类型约束见对应对象 |
| `report_ref` | [Ref](./Ref.md) | 是 | 逐项VerificationReport | 类型约束见对应对象 |
| `proposal_ref` | [Ref](./Ref.md) | 是 | 候选DeliveryProposal | 类型约束见对应对象 |
| `source_pins` | 数组&lt;[EvaluationSourcePin](./EvaluationSourcePin.md)&gt; | 是 | 终态前重新读取的实际来源 | 最少项 `0`；最多项 `128` |
| `tool_activity_ids` | 数组&lt;[ID](./ID.md)&gt; | 否 | 评估时该Run所有已登记工具动作；终态再核对完整集合 | 最少项 `0`；最多项 `16` |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 运行时约束

- Bundle本身不是写权限；独立控制器以当前Run版本提交终态。

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
  "instance_id": "example_001",
  "frame_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "contract_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "artifact_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "report_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "proposal_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "source_pins": []
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.CompletionBundle`。
