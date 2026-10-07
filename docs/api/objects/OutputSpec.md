# OutputSpec

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：Agent执行与协作。

一个可交付结果要求。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `id` | [ID](./ID.md) | 是 | 成果要求ID | 类型约束见对应对象 |
| `kind` | [NonEmptyText](./NonEmptyText.md) | 是 | 成果类型 | 类型约束见对应对象 |
| `description` | [NonEmptyText](./NonEmptyText.md) | 是 | 内容/用途 | 类型约束见对应对象 |
| `required` | [Bool](./Bool.md) | 是 | 必需 | 类型约束见对应对象 |
| `schema_ref` | [Ref](./Ref.md) | 否 | 结构检查schema | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "id": "example_001",
  "kind": "example_001",
  "description": "example_001",
  "required": true
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.OutputSpec`。
