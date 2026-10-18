# QualityCase

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：配置与共享基础设施。



[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `id` | string | 是 | 见类型说明 | 最少字符 `1`；最多字符 `128`；正则 `^[A-Za-z0-9][A-Za-z0-9._:-]*$` |
| `version` | string | 是 | 见类型说明 | 最少字符 `1`；最多字符 `128`；正则 `^[A-Za-z0-9][A-Za-z0-9._:-]*$` |
| `split` | enum: `revision` / `holdout` | 是 | 见类型说明 | — |
| `category` | enum: `office` / `academic` / `technical` / `missing_material` / `reasonable_ambiguity` / `correction` | 是 | 见类型说明 | — |
| `prompt` | string | 是 | 见类型说明 | 最少字符 `1`；最多字符 `16384` |
| `rubric` | [QualityRubric](./QualityRubric.md) | 是 | 见类型说明 | 类型约束见对应对象 |
| `evidence` | 数组&lt;[QualityEvidence](./QualityEvidence.md)&gt; | 是 | 见类型说明 | 最多项 `16` |
| `review_status` | enum: `needs_human_review` / `human_verified` | 是 | 见类型说明 | — |
| `human_verification` | 至少一个分支 | 是 | 见类型说明 | — |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 运行时约束

- 原来源/回答版本绑定；认证用户独立判断，未知不当作通过。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
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
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.QualityCase`。
