# ToolSpec

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：工具运行。

控制层注册的工具契约；描述检索不替代调用校验。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `id` | [ID](./ID.md) | 是 | 稳定工具名 | 类型约束见对应对象 |
| `version` | [Version](./Version.md) | 是 | 固定schema版本 | 类型约束见对应对象 |
| `description` | [NonEmptyText](./NonEmptyText.md) | 是 | 用途、限制和适用条件 | 类型约束见对应对象 |
| `input_schema` | [Schema](./Schema.md) | 是 | 参数schema | 类型约束见对应对象 |
| `output_schema` | [Schema](./Schema.md) | 是 | 业务结果schema | 类型约束见对应对象 |
| `categories` | 数组&lt;[ID](./ID.md)&gt; | 是 | 类别 | 最少项 `0`；最多项 `256` |
| `required_capabilities` | 数组&lt;[ID](./ID.md)&gt; | 是 | 权限需求 | 最少项 `0`；最多项 `256` |
| `effect` | [EffectKind](./EffectKind.md) | 是 | 效果类别 | 类型约束见对应对象 |
| `provider_ref` | [Ref](./Ref.md) | 是 | 有效提供方 | 类型约束见对应对象 |
| `equivalence_contract_ref` | [Ref](./Ref.md) | 否 | 严格等价替代约束 | 类型约束见对应对象 |
| `retry_policy_ref` | [Ref](./Ref.md) | 是 | 恢复上限 | 类型约束见对应对象 |
| `feature_flag` | [ID](./ID.md) | 否 | 产品开关 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "id": "example_001",
  "version": "example_001",
  "description": "example_001",
  "input_schema": {},
  "output_schema": {},
  "categories": [],
  "required_capabilities": [],
  "effect": "read",
  "provider_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "retry_policy_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  }
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.ToolSpec`。
