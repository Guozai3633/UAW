# ResolvedModelConfig

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：模型调用。

实际调用配置随用量记录。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `model_id` | [ID](./ID.md) | 是 | 实际目录模型 | 类型约束见对应对象 |
| `catalog_revision` | [Revision](./Revision.md) | 是 | 目录版本 | 类型约束见对应对象 |
| `provider_ref` | [Ref](./Ref.md) | 是 | 绑定版本 | 类型约束见对应对象 |
| `policy_ref` | [Ref](./Ref.md) | 是 | 模型政策 | 类型约束见对应对象 |
| `max_output_tokens` | [Count](./Count.md) | 是 | 输出预算 | 类型约束见对应对象 |
| `reasoning_level` | [NonEmptyText](./NonEmptyText.md) | 否 | 管理员登记支持值 | 类型约束见对应对象 |
| `temperature` | [Temperature](./Temperature.md) | 否 | 提供方支持才可配置 | 类型约束见对应对象 |
| `provider_model_name` | [NonEmptyText](./NonEmptyText.md) | 否 | 实际供应商请求/响应模型名称；别名需管理员批准。 | 类型约束见对应对象 |
| `response_model_name` | [NonEmptyText](./NonEmptyText.md) | 否 | 实际供应商请求/响应模型名称；别名需管理员批准。 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "model_id": "example_001",
  "catalog_revision": 0,
  "provider_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "policy_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "max_output_tokens": 0
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.ResolvedModelConfig`。
