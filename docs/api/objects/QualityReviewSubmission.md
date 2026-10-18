# QualityReviewSubmission

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：配置与共享基础设施。



[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `schema_version` | 常量 `uaw.human-review-submission.v1` | 是 | 见类型说明 | — |
| `packet_sha256` | string | 是 | 见类型说明 | 正则 `^[0-9a-f]{64}$` |
| `reviewer_id` | string | 是 | 见类型说明 | 最少字符 `1`；最多字符 `128`；正则 `^[A-Za-z0-9][A-Za-z0-9._:-]*$` |
| `reviewed_at` | string | 是 | 见类型说明 | 最少字符 `20`；最多字符 `40` |
| `human_attested` | boolean | 是 | 见类型说明 | — |
| `items` | 数组&lt;[QualitySubmittedReview](./QualitySubmittedReview.md)&gt; | 是 | 见类型说明 | 最少项 `1`；最多项 `128` |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 运行时约束

- 原来源/回答版本绑定；认证用户独立判断，未知不当作通过。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
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
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.QualityReviewSubmission`。
