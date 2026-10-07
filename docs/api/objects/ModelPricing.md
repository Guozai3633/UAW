# ModelPricing

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：模型调用。

账单估算使用管理员核验的固定价格版本。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `id` | [ID](./ID.md) | 是 | 价格 | 类型约束见对应对象 |
| `version` | [Version](./Version.md) | 是 | 版本 | 类型约束见对应对象 |
| `currency` | [Currency](./Currency.md) | 是 | 币种 | 类型约束见对应对象 |
| `input_per_million_tokens` | [Decimal](./Decimal.md) | 是 | 输入单价 | 类型约束见对应对象 |
| `output_per_million_tokens` | [Decimal](./Decimal.md) | 是 | 输出单价 | 类型约束见对应对象 |
| `cached_input_per_million_tokens` | [Decimal](./Decimal.md) | 否 | 提供方缓存价格 | 类型约束见对应对象 |
| `effective_at` | [Timestamp](./Timestamp.md) | 是 | 生效 | 类型约束见对应对象 |
| `source_ref` | [Ref](./Ref.md) | 是 | 管理员依据 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "id": "example_001",
  "version": "example_001",
  "currency": "CNY",
  "input_per_million_tokens": "0",
  "output_per_million_tokens": "0",
  "effective_at": "2026-10-07T02:00:00Z",
  "source_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  }
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.ModelPricing`。
