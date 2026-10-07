# VerificationReport

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：Agent执行与协作。

结构检查+真实执行+语义判定，不替代用户审阅。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `id` | [ID](./ID.md) | 是 | 报告 | 类型约束见对应对象 |
| `contract_ref` | [Ref](./Ref.md) | 是 | 交付要求 | 类型约束见对应对象 |
| `target_refs` | 数组&lt;[Ref](./Ref.md)&gt; | 是 | 成果版本 | 最少项 `0`；最多项 `256` |
| `checks` | 数组&lt;[VerificationCheck](./VerificationCheck.md)&gt; | 是 | 具体检查 | 最少项 `0`；最多项 `256` |
| `verdicts` | 数组&lt;[RequirementVerdict](./RequirementVerdict.md)&gt; | 是 | 逐要求结果 | 最少项 `0`；最多项 `256` |
| `outcome` | [Outcome](./Outcome.md) | 是 | 总体结果 | 类型约束见对应对象 |
| `limitations` | 数组&lt;[NonEmptyText](./NonEmptyText.md)&gt; | 是 | 缺口 | 最少项 `0`；最多项 `256` |
| `reviewer_model_config_ref` | [Ref](./Ref.md) | 否 | 语义评审模型 | 类型约束见对应对象 |
| `created_at` | [Timestamp](./Timestamp.md) | 是 | 生成时间 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
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
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.VerificationReport`。
