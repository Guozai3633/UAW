# quality.reviews.submit

状态：契约0.1，待实现。类别：用户与管理端 HTTP API。所属：配置与共享基础设施。

认证网页质量审阅写入；要求 CAS 和原目标绑定。

[分类索引](../HTTP.md) · [统一规则](../CONVENTIONS.md) · [实际范围](../../implementation/README.md)

## 调用入口

`POST /v1/quality/reviews/{review_id}/submission`；认证：`user`。

请求体是 `{meta, payload}`；路径ID从path取得，不重复写入payload。OpenAPI记录实际线上字段位置；下方输入对象是服务合成的业务请求。

## 输入

[QualityReviewsSubmitRequest](../objects/QualityReviewsSubmitRequest.md)；每个字段的类型、必填性、默认注解、限制和分支见对象页。

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `review_id` | string | 是 | 见类型 |
| `packet_sha256` | string | 是 | 见类型 |
| `judgments` | 数组&lt;[QualityJudgment](../objects/QualityJudgment.md)&gt; | 是 | 见类型 |
| `human_attested` | boolean | 是 | 见类型 |

## 输出

[HttpQualityReviewsSubmitResult](../objects/HttpQualityReviewsSubmitResult.md) 为完整返回结构。`kind=ok` 的payload是 [QualityReviewView](../objects/QualityReviewView.md)。`waiting`带wait_ref，其他非成功状态带Failure，不能用空对象假装成功。

| payload字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `id` | string | 是 | 见类型 |
| `revision` | integer | 是 | 见类型 |
| `title` | string | 是 | 见类型 |
| `created_at` | string | 是 | 见类型 |
| `updated_at` | string | 是 | 见类型 |
| `origin` | [QualityOrigin](../objects/QualityOrigin.md) | 是 | 见类型 |
| `packet` | [QualityReviewPacket](../objects/QualityReviewPacket.md) | 是 | 见类型 |
| `packet_sha256` | string | 是 | 见类型 |
| `targets` | 数组&lt;[QualityTarget](../objects/QualityTarget.md)&gt; | 是 | 见类型 |
| `status` | enum: `draft` / `submitted` | 是 | 见类型 |
| `judgments` | 数组&lt;[QualityJudgment](../objects/QualityJudgment.md)&gt; | 是 | 见类型 |
| `submission` | 至少一个分支 | 是 | 见类型 |

## 约束与提交

- 效果分类：`write`。
- 认证/上下文：`user`；范围及权限由服务端或Runner取得。
- 请求/动作ID去重与CAS按[统一规则](../CONVENTIONS.md)执行，重复ID不同参数必须冲突。
- 本人归属；写入要求独立对象 CAS/幂等；不修改 Run。

## 错误、等待、取消

错误对象是 [Failure](../objects/Failure.md)；统一分类：schema_invalid / permission_denied / feature_disabled / revision_conflict / stale_resource / dependency_unavailable / budget_exceeded / deadline_exceeded / cancelled / unknown_effect。实际Runtime需要把业务错误映射到此对象；上述分类不会代替明确failed_phase和恢复提示。

只读可在有界策略内重试；写失败先核对动作账本，效果unknown时禁止盲重试；waiting通过审批决定、用户输入、process.poll或agents.wait推进。取消只停止后续执行，已有效果如实保留。

## 请求示例

示例展示结构；不代表这些示例引用存在。

```json
{
  "meta": {
    "request_id": "request_001",
    "schema_version": "0.1",
    "expected_revision": 0
  },
  "payload": {
    "packet_sha256": "example_001",
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
    "human_attested": true
  }
}
```

## 成功结构示例

```json
{
  "kind": "ok",
  "payload": {
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
    }
  },
  "output_refs": []
}
```

## 拒绝结构示例

```json
{
  "kind": "denied",
  "output_refs": [],
  "failure": {
    "code": "permission_denied",
    "category": "authorization",
    "message": "当前主体没有本动作所需权限。",
    "retryable": false,
    "failed_phase": "policy_gate",
    "recover_hint": "取得真实授权后重新检查；不能通过换工具绕过。"
  }
}
```

## 模块与目录

| 节点 | 详细策略 | 计划代码位置 |
| --- | --- | --- |
| `support.evaluation` | [开发设计](../../../docs/design/components/support-evaluation.md) | `src/uaw/shared/evaluation.py` |

[接口机器目录](../../../contracts/interfaces.json) · [统一对象schema](../../../contracts/uaw.schema.json)
