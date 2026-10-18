# QualityTarget

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：配置与共享基础设施。



[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `binding` | [QualityReviewTarget](./QualityReviewTarget.md) | 是 | 见类型说明 | 类型约束见对应对象 |
| `case` | [QualityCase](./QualityCase.md) | 是 | 见类型说明 | 类型约束见对应对象 |
| `answer` | [QualityAnswer](./QualityAnswer.md) | 是 | 见类型说明 | 类型约束见对应对象 |
| `verifications` | 数组&lt;[QualityObservation](./QualityObservation.md)&gt; | 是 | 见类型说明 | 最多项 `32` |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 运行时约束

- 原来源/回答版本绑定；认证用户独立判断，未知不当作通过。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
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
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.QualityTarget`。
