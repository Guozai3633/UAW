# HttpQualityReviewsGetResult

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：配置与共享基础设施。

该接口的状态结果；ok才携带完整业务payload。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `kind` | enum: `ok` / `waiting` / `missing` / `denied` / `conflict` / `stale` / `failed` / `cancelled` | 是 | 接口状态 | — |
| `payload` | [QualityReviewView](./QualityReviewView.md) | 否 | ok的业务结果 | 类型约束见对应对象 |
| `output_refs` | 数组&lt;[Ref](./Ref.md)&gt; | 是 | 关联真实资源 | 最少项 `0`；最多项 `256` |
| `revision` | [Revision](./Revision.md) | 否 | 本次提交/读取的域版本 | 类型约束见对应对象 |
| `failure` | [Failure](./Failure.md) | 否 | 失败状态的明确原因 | 类型约束见对应对象 |
| `wait_ref` | [Ref](./Ref.md) | 否 | waiting时审批/进程/用户问题引用 | 类型约束见对应对象 |
| `usage_ref` | [Ref](./Ref.md) | 否 | 发生消耗时真实统计 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## allOf结构规则

```json
{
  "allOf": [
    {
      "if": {
        "properties": {
          "kind": {
            "const": "ok"
          }
        },
        "required": [
          "kind"
        ]
      },
      "then": {
        "required": [
          "payload"
        ],
        "not": {
          "required": [
            "failure"
          ]
        }
      }
    },
    {
      "if": {
        "properties": {
          "kind": {
            "const": "waiting"
          }
        },
        "required": [
          "kind"
        ]
      },
      "then": {
        "required": [
          "wait_ref"
        ],
        "not": {
          "required": [
            "payload"
          ]
        }
      }
    },
    {
      "if": {
        "properties": {
          "kind": {
            "enum": [
              "missing",
              "denied",
              "conflict",
              "stale",
              "failed",
              "cancelled"
            ]
          }
        },
        "required": [
          "kind"
        ]
      },
      "then": {
        "required": [
          "failure"
        ],
        "not": {
          "required": [
            "payload"
          ]
        }
      }
    }
  ]
}
```

## 运行时约束

- ok必需payload且不含failure；waiting必需wait_ref；其他状态必需failure；取消不回滚已确认外部动作。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "kind": "ok",
  "output_refs": [],
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
  }
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.HttpQualityReviewsGetResult`。
