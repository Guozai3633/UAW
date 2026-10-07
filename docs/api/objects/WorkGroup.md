# WorkGroup

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：Agent执行与协作。

独立性是建议，调度器仍检查读写集合。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `id` | [ID](./ID.md) | 是 | 工作组 | 类型约束见对应对象 |
| `goal` | [NonEmptyText](./NonEmptyText.md) | 是 | 分工目标 | 类型约束见对应对象 |
| `input_refs` | 数组&lt;[Ref](./Ref.md)&gt; | 是 | 已知输入 | 最少项 `0`；最多项 `256` |
| `read_refs` | 数组&lt;[Ref](./Ref.md)&gt; | 是 | 读集 | 最少项 `0`；最多项 `256` |
| `write_refs` | 数组&lt;[Ref](./Ref.md)&gt; | 是 | 写集 | 最少项 `0`；最多项 `256` |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "id": "example_001",
  "goal": "example_001",
  "input_refs": [],
  "read_refs": [],
  "write_refs": []
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.WorkGroup`。
