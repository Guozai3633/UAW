# Citation

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：上下文与资料。

一句主张到实际资料位置的映射。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `claim_id` | [ID](./ID.md) | 是 | 结论锚点 | 类型约束见对应对象 |
| `source_ref` | [Ref](./Ref.md) | 是 | 固定版本和位置 | 类型约束见对应对象 |
| `support` | [CitationSupport](./CitationSupport.md) | 是 | 支持程度 | 类型约束见对应对象 |
| `explanation` | [Text](./Text.md) | 是 | 推断、冲突或限制 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "claim_id": "example_001",
  "source_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "support": "direct",
  "explanation": "example_001"
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.Citation`。
