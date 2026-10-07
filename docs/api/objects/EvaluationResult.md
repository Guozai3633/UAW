# EvaluationResult

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：配置与共享基础设施。

成本统计包含失败、重试和用户返工。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `id` | [ID](./ID.md) | 是 | 评测 | 类型约束见对应对象 |
| `candidate_manifest_ref` | [Ref](./Ref.md) | 是 | 候选 | 类型约束见对应对象 |
| `baseline_manifest_ref` | [Ref](./Ref.md) | 是 | 基线 | 类型约束见对应对象 |
| `dataset_ref` | [Ref](./Ref.md) | 是 | 固定样本 | 类型约束见对应对象 |
| `accepted_count` | [Count](./Count.md) | 是 | 可接受成果数量 | 类型约束见对应对象 |
| `attempt_count` | [Count](./Count.md) | 是 | 所有尝试 | 类型约束见对应对象 |
| `total_usage_ref` | [Ref](./Ref.md) | 是 | 总消耗 | 类型约束见对应对象 |
| `report_ref` | [Ref](./Ref.md) | 是 | 质量/耗时报告 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "id": "example_001",
  "candidate_manifest_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "baseline_manifest_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "dataset_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "accepted_count": 0,
  "attempt_count": 0,
  "total_usage_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "report_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  }
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.EvaluationResult`。
