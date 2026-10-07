# EquivalenceContract

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：工具运行。

提供方自动切换前的严格等价登记。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `id` | [ID](./ID.md) | 是 | 契约 | 类型约束见对应对象 |
| `version` | [Version](./Version.md) | 是 | 版本 | 类型约束见对应对象 |
| `tool_ref` | [Ref](./Ref.md) | 是 | 同一能力契约 | 类型约束见对应对象 |
| `provider_refs` | 数组&lt;[Ref](./Ref.md)&gt; | 是 | 经过核验的提供方 | 最少项 `0`；最多项 `256` |
| `input_schema_ref` | [Ref](./Ref.md) | 是 | 相同参数语义 | 类型约束见对应对象 |
| `output_schema_ref` | [Ref](./Ref.md) | 是 | 相同结果语义 | 类型约束见对应对象 |
| `information_scope_ref` | [Ref](./Ref.md) | 是 | 相同信息范围 | 类型约束见对应对象 |
| `effect` | [EffectKind](./EffectKind.md) | 是 | 相同效果 | 类型约束见对应对象 |
| `idempotency_namespace` | [ID](./ID.md) | 是 | 同逻辑动作命名空间 | 类型约束见对应对象 |
| `verification_refs` | 数组&lt;[Ref](./Ref.md)&gt; | 是 | 等价测试证据 | 最少项 `0`；最多项 `256` |
| `state` | [ProviderState](./ProviderState.md) | 是 | 是否已批准 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 运行时约束

- 网页摘要与原文读取不能默认等价；写提供方切换还须业务幂等可确认。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "id": "example_001",
  "version": "example_001",
  "tool_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "provider_refs": [],
  "input_schema_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "output_schema_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "information_scope_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "effect": "read",
  "idempotency_namespace": "example_001",
  "verification_refs": [],
  "state": "draft"
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.EquivalenceContract`。
