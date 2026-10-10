# RunDeliveryView

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：运行与会话。

真实成果、合同、逐项核验、完成提案的固定视图；不返回执行上下文。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `run_id` | [ID](./ID.md) | 是 | 所属Run | 类型约束见对应对象 |
| `bundle_ref` | [Ref](./Ref.md) | 是 | 固定Bundle | 类型约束见对应对象 |
| `artifact_ref` | [Ref](./Ref.md) | 是 | 固定成果 | 类型约束见对应对象 |
| `artifact` | [ArtifactRecord](./ArtifactRecord.md) | 是 | 成果记录 | 类型约束见对应对象 |
| `content` | [ArtifactPreviewText](./ArtifactPreviewText.md) | 是 | 实际正文 | 类型约束见对应对象 |
| `contract_ref` | [Ref](./Ref.md) | 是 | 固定合同 | 类型约束见对应对象 |
| `contract` | [Contract](./Contract.md) | 是 | 原要求合同 | 类型约束见对应对象 |
| `report_ref` | [Ref](./Ref.md) | 是 | 固定报告 | 类型约束见对应对象 |
| `report` | [VerificationReport](./VerificationReport.md) | 是 | 逐项报告 | 类型约束见对应对象 |
| `proposal_ref` | [Ref](./Ref.md) | 是 | 固定提案 | 类型约束见对应对象 |
| `proposal` | [DeliveryProposal](./DeliveryProposal.md) | 是 | 候选提案 | 类型约束见对应对象 |
| `requires_acceptance` | [Bool](./Bool.md) | 是 | 合同要求用户接受 | 类型约束见对应对象 |
| `stale` | [Bool](./Bool.md) | 是 | 相对于当前任务版本过时 | 类型约束见对应对象 |
| `acceptance` | [CompletionAcceptance](./CompletionAcceptance.md) | 否 | 实际用户决定 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "run_id": "example_001",
  "bundle_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "artifact_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "artifact": {
    "id": "example_001",
    "version": "example_001",
    "title": "example_001",
    "format_kind": "example_001",
    "media_type": "example_001",
    "content_ref": {
      "kind": "web",
      "id": "example_001",
      "version": "example_001"
    },
    "size_bytes": 0,
    "content_hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
    "provenance_refs": [],
    "verification_refs": [],
    "created_at": "2026-10-07T02:00:00Z"
  },
  "content": "example_001",
  "contract_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "contract": {
    "goal": "example_001",
    "requirements": [],
    "outputs": [],
    "version": "example_001"
  },
  "report_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "report": {
    "id": "example_001",
    "contract_ref": {
      "kind": "web",
      "id": "example_001",
      "version": "example_001"
    },
    "target_refs": [],
    "checks": [],
    "verdicts": [],
    "outcome": "succeeded",
    "limitations": [],
    "created_at": "2026-10-07T02:00:00Z"
  },
  "proposal_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "proposal": {
    "run_ref": {
      "kind": "web",
      "id": "example_001",
      "version": "example_001"
    },
    "contract_ref": {
      "kind": "web",
      "id": "example_001",
      "version": "example_001"
    },
    "outcome": "succeeded",
    "artifact_refs": [],
    "report_ref": {
      "kind": "web",
      "id": "example_001",
      "version": "example_001"
    },
    "unresolved_effect_refs": [],
    "created_at": "2026-10-07T02:00:00Z"
  },
  "requires_acceptance": true,
  "stale": true
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.RunDeliveryView`。
