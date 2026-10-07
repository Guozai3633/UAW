# InternalSupportEvaluationRequest

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：配置与共享基础设施。

离线质量评测的私有阶段输入。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `candidate_manifest` | [Ref](./Ref.md) | 是 | 待测候选系统/方法/适配器版本清单。 | 类型约束见对应对象 |
| `baseline_manifest` | [Ref](./Ref.md) | 是 | 同任务预算基线的系统版本清单。 | 类型约束见对应对象 |
| `dataset_version` | [Ref](./Ref.md) | 是 | 固定任务样本版本，候选与基线须一致。 | 类型约束见对应对象 |
| `fixture_environment` | [Ref](./Ref.md) | 是 | 固定评测环境、输入初态与允许副作用。 | 类型约束见对应对象 |
| `grader_config` | [Ref](./Ref.md) | 是 | 固定评分方法与人工/语义评审政策。 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 运行时约束

- 评测输入、评分器和报告版本不可变；一次运行验收不替代离线系统比较。
- 服务端注入可信上下文，不通过HTTP或LLM工具直接访问。

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

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.InternalSupportEvaluationRequest`。
