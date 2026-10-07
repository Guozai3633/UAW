# TaskFrame

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：任务理解。

版本化任务理解。原文保持独立，理解不能覆盖原文。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `task_id` | [ID](./ID.md) | 是 | 关联任务 | 类型约束见对应对象 |
| `revision` | [Revision](./Revision.md) | 是 | 当前理解版本 | 类型约束见对应对象 |
| `original_input_ref` | [UserInputRef](./UserInputRef.md) | 是 | 原始用户输入 | 类型约束见对应对象 |
| `patch_refs` | 数组&lt;[Ref](./Ref.md)&gt; | 是 | 运行中追加要求 | 最少项 `0`；最多项 `256` |
| `goal` | string | 是 | 本轮以完整原文及追加要求作为任务基准；AI摘要单独放summary。 | 最少字符 `1`；最多字符 `131072` |
| `constraints` | 数组&lt;[Constraint](./Constraint.md)&gt; | 是 | 约束及来源 | 最少项 `0`；最多项 `256` |
| `output_specs` | 数组&lt;[OutputSpec](./OutputSpec.md)&gt; | 是 | 成果要求 | 最少项 `0`；最多项 `256` |
| `assumptions` | 数组&lt;[NonEmptyText](./NonEmptyText.md)&gt; | 是 | 明确标记的假设 | 最少项 `0`；最多项 `256` |
| `unresolved` | 数组&lt;[NonEmptyText](./NonEmptyText.md)&gt; | 是 | 未解问题 | 最少项 `0`；最多项 `256` |
| `evidence_refs` | 数组&lt;[Ref](./Ref.md)&gt; | 是 | 已读取材料 | 最少项 `0`；最多项 `256` |
| `created_at` | [Timestamp](./Timestamp.md) | 是 | 版本提交时间 | 类型约束见对应对象 |
| `summary` | [NonEmptyText](./NonEmptyText.md) | 否 | AI理解的提示摘要，不授权动作、不替代完整原文。 | 类型约束见对应对象 |
| `input_revision` | [Revision](./Revision.md) | 否 | 生成时的Run输入集合版本；旧理解不得覆盖新输入。 | 类型约束见对应对象 |
| `semantic_parse_ref` | [Ref](./Ref.md) | 否 | 有界模型提案及来源位置，保留模型回执。 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "task_id": "example_001",
  "revision": 0,
  "original_input_ref": {
    "kind": "input",
    "id": "example_001",
    "version": "example_001"
  },
  "patch_refs": [],
  "goal": "example_001",
  "constraints": [],
  "output_specs": [],
  "assumptions": [],
  "unresolved": [],
  "evidence_refs": [],
  "created_at": "2026-10-07T02:00:00Z"
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.TaskFrame`。
