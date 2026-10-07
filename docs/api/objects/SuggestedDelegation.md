# SuggestedDelegation

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：Agent执行与协作。

执行评估中的分工建议，尚未分配预算或启动实例。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `definition_ref` | [Ref](./Ref.md) | 否 | 候选角色 | 类型约束见对应对象 |
| `goal` | [NonEmptyText](./NonEmptyText.md) | 是 | 子目标 | 类型约束见对应对象 |
| `input_refs` | 数组&lt;[Ref](./Ref.md)&gt; | 是 | 已知资料 | 最少项 `0`；最多项 `256` |
| `output_contract` | [Contract](./Contract.md) | 是 | 验收 | 类型约束见对应对象 |
| `start_condition` | [StartCondition](./StartCondition.md) | 是 | 何时可启动 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "goal": "example_001",
  "input_refs": [],
  "output_contract": {
    "goal": "example_001",
    "requirements": [],
    "outputs": [],
    "version": "example_001"
  },
  "start_condition": "inputs_available"
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.SuggestedDelegation`。
