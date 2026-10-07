# PreservationSpec

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：上下文与资料。

压缩必须保留的任务与证据集合。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `required_refs` | 数组&lt;[Ref](./Ref.md)&gt; | 是 | 不可丢失来源 | 最少项 `0`；最多项 `256` |
| `exact_strings` | 数组&lt;[NonEmptyText](./NonEmptyText.md)&gt; | 是 | 数字、路径等精确文本 | 最少项 `0`；最多项 `256` |
| `requirement_ids` | 数组&lt;[ID](./ID.md)&gt; | 是 | 关键约束 | 最少项 `0`；最多项 `256` |
| `pending_action_refs` | 数组&lt;[Ref](./Ref.md)&gt; | 是 | 未决动作 | 最少项 `0`；最多项 `256` |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "required_refs": [],
  "exact_strings": [],
  "requirement_ids": [],
  "pending_action_refs": []
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.PreservationSpec`。
