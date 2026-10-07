# Requirement

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：Agent执行与协作。

用户/政策验收要求。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `id` | [ID](./ID.md) | 是 | 要求ID | 类型约束见对应对象 |
| `text` | [NonEmptyText](./NonEmptyText.md) | 是 | 语义内容 | 类型约束见对应对象 |
| `mandatory` | [Bool](./Bool.md) | 是 | 是否必需 | 类型约束见对应对象 |
| `source_refs` | 数组&lt;[Ref](./Ref.md)&gt; | 是 | 用户或政策来源 | 最少项 `1`；最多项 `64` |
| `evidence_kinds` | 数组&lt;[NonEmptyText](./NonEmptyText.md)&gt; | 否 | 可接受证据类别 | 最少项 `0`；最多项 `32` |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "id": "example_001",
  "text": "example_001",
  "mandatory": true,
  "source_refs": [
    {
      "kind": "web",
      "id": "example_001",
      "version": "example_001"
    }
  ]
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.Requirement`。
