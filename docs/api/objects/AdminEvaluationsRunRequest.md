# AdminEvaluationsRunRequest

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：配置与共享基础设施。

固定样本评测。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `candidate_manifest` | [Ref](./Ref.md) | 是 | 候选 | 类型约束见对应对象 |
| `baseline_manifest` | [Ref](./Ref.md) | 是 | 基线 | 类型约束见对应对象 |
| `dataset_version` | [Ref](./Ref.md) | 是 | 样本 | 类型约束见对应对象 |
| `fixture_environment` | [Ref](./Ref.md) | 是 | 环境 | 类型约束见对应对象 |
| `grader_config` | [Ref](./Ref.md) | 是 | 评分配置 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "candidate_manifest": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "baseline_manifest": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "dataset_version": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "fixture_environment": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "grader_config": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  }
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.AdminEvaluationsRunRequest`。
