# QualityReviewRecord

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：配置与共享基础设施。



[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `id` | string | 是 | 见类型说明 | 最少字符 `1`；最多字符 `128`；正则 `^[A-Za-z0-9][A-Za-z0-9._:-]*$` |
| `revision` | integer | 是 | 见类型说明 | ≥ `1` |
| `title` | string | 是 | 见类型说明 | 最少字符 `1`；最多字符 `200` |
| `created_at` | string | 是 | 见类型说明 | 最少字符 `20`；最多字符 `40` |
| `updated_at` | string | 是 | 见类型说明 | 最少字符 `20`；最多字符 `40` |
| `origin` | [QualityOrigin](./QualityOrigin.md) | 是 | 见类型说明 | 类型约束见对应对象 |
| `packet` | [QualityReviewPacket](./QualityReviewPacket.md) | 是 | 见类型说明 | 类型约束见对应对象 |
| `packet_sha256` | string | 是 | 见类型说明 | 正则 `^[0-9a-f]{64}$` |
| `targets` | 数组&lt;[QualityTarget](./QualityTarget.md)&gt; | 是 | 见类型说明 | 最少项 `1`；最多项 `8` |
| `status` | enum: `draft` / `submitted` | 是 | 见类型说明 | — |
| `judgments` | 数组&lt;[QualityJudgment](./QualityJudgment.md)&gt; | 是 | 见类型说明 | 最少项 `1`；最多项 `8` |
| `submission` | 至少一个分支 | 是 | 见类型说明 | — |
| `files` | [QualityFiles](./QualityFiles.md) | 是 | 见类型说明 | 类型约束见对应对象 |
| `exported_files` | 至少一个分支 | 是 | 见类型说明 | — |
| `basis` | enum: `human_evidence_review` / `controlled_test` | 是 | 见类型说明 | — |
| `registered_by` | string | 是 | 见类型说明 | 最少字符 `1`；最多字符 `128`；正则 `^[A-Za-z0-9][A-Za-z0-9._:-]*$` |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 运行时约束

- 原来源/回答版本绑定；认证用户独立判断，未知不当作通过。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "id": "example_001",
  "revision": 1,
  "title": "example_001",
  "created_at": "example_001xxxxxxxxx",
  "updated_at": "example_001xxxxxxxxx",
  "origin": {
    "kind": "actual_run",
    "principal_id": "example_001",
    "run_id": "example_001",
    "run_revision": 1,
    "input_revision": 1,
    "source_commit": "example_001"
  },
  "packet": {
    "schema_version": "uaw.human-review-packet.v1",
    "created_at": "example_001xxxxxxxxx",
    "input_sha256": [],
    "targets": [
      {
        "case_id": "example_001",
        "case_version": "example_001",
        "case_sha256": "example_001",
        "manifest_id": "example_001",
        "attempt_id": "example_001",
        "output_sha256": "example_001"
      }
    ]
  },
  "packet_sha256": "example_001",
  "targets": [
    {
      "binding": {
        "case_id": "example_001",
        "case_version": "example_001",
        "case_sha256": "example_001",
        "manifest_id": "example_001",
        "attempt_id": "example_001",
        "output_sha256": "example_001"
      },
      "case": {
        "id": "example_001",
        "version": "example_001",
        "split": "revision",
        "category": "office",
        "prompt": "example_001",
        "rubric": {
          "expected_behavior": "answer",
          "required_facts": [
            "example_001"
          ],
          "allowed_assumptions": [],
          "retained_requirements": [],
          "critical": true
        },
        "evidence": [],
        "review_status": "needs_human_review",
        "human_verification": {
          "reviewer_id": "example_001",
          "reviewed_at": "example_001xxxxxxxxx",
          "rubric_sha256": "example_001",
          "evidence_sha256": [],
          "record_locator": "example_001"
        }
      },
      "answer": {
        "decision": "reply",
        "text": "example_001",
        "evidence": []
      },
      "verifications": []
    }
  ],
  "status": "draft",
  "judgments": [
    {
      "case_id": "example_001",
      "attempt_id": "example_001",
      "case_review": "verified",
      "evidence_reviewed": true,
      "answer_correct": true,
      "unnecessary_block": true,
      "unsupported_execution": true,
      "requirements_preserved": true,
      "acceptable": true,
      "critical_error": true,
      "fabricated_evidence": true,
      "notes": "example_001"
    }
  ],
  "submission": {
    "schema_version": "uaw.human-review-submission.v1",
    "packet_sha256": "example_001",
    "reviewer_id": "example_001",
    "reviewed_at": "example_001xxxxxxxxx",
    "human_attested": true,
    "items": [
      {
        "case_id": "example_001",
        "attempt_id": "example_001",
        "case_review": "verified",
        "evidence_reviewed": true,
        "labels": {
          "answer_correct": true,
          "unnecessary_block": true,
          "unsupported_execution": true,
          "requirements_preserved": true,
          "acceptable": true,
          "critical_error": true
        },
        "notes": "example_001"
      }
    ]
  },
  "files": {
    "suite": "example_001",
    "manifest": "example_001",
    "observations": "example_001",
    "reviews": "example_001"
  },
  "exported_files": {
    "suite": "example_001",
    "manifest": "example_001",
    "observations": "example_001",
    "reviews": "example_001"
  },
  "basis": "human_evidence_review",
  "registered_by": "example_001"
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.QualityReviewRecord`。
