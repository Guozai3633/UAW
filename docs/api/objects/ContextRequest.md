# ContextRequest

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：上下文与资料。

统一上下文构建入口，purpose决定启用哪些策略。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `purpose` | [Purpose](./Purpose.md) | 是 | 目的 | 类型约束见对应对象 |
| `source_refs` | 数组&lt;[Ref](./Ref.md)&gt; | 是 | 来源 | 最少项 `0`；最多项 `256` |
| `model_policy_ref` | [Ref](./Ref.md) | 是 | 当前模型 | 类型约束见对应对象 |
| `output_reserve` | [Count](./Count.md) | 是 | 输出预留 | 类型约束见对应对象 |
| `tool_reserve` | [Count](./Count.md) | 是 | 工具预留 | 类型约束见对应对象 |
| `preserve` | [PreservationSpec](./PreservationSpec.md) | 是 | 保护要求 | 类型约束见对应对象 |
| `expected_epoch` | [Revision](./Revision.md) | 是 | 上下文纪元 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "purpose": "draft_preview",
  "source_refs": [],
  "model_policy_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "output_reserve": 0,
  "tool_reserve": 0,
  "preserve": {
    "required_refs": [],
    "exact_strings": [],
    "requirement_ids": [],
    "pending_action_refs": []
  },
  "expected_epoch": 0
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.ContextRequest`。
