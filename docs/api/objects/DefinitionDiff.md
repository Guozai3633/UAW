# DefinitionDiff

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：Agent执行与协作。

角色历史比较。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `definition_id` | [ID](./ID.md) | 是 | 角色 | 类型约束见对应对象 |
| `base_ref` | [Ref](./Ref.md) | 是 | 基线 | 类型约束见对应对象 |
| `target_ref` | [Ref](./Ref.md) | 是 | 目标 | 类型约束见对应对象 |
| `changed_fields` | 数组&lt;[NonEmptyText](./NonEmptyText.md)&gt; | 是 | 改变字段 | 最少项 `0`；最多项 `256` |
| `change_set_ref` | [Ref](./Ref.md) | 是 | 可审阅内容 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "definition_id": "example_001",
  "base_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "target_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "changed_fields": [],
  "change_set_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  }
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.DefinitionDiff`。
