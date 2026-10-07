# Failure

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：公共协议。

类型化失败，不携带秘密与隐藏思维。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `code` | [ID](./ID.md) | 是 | 稳定错误码 | 类型约束见对应对象 |
| `category` | [FailureCategory](./FailureCategory.md) | 是 | 错误类别 | 类型约束见对应对象 |
| `message` | [NonEmptyText](./NonEmptyText.md) | 是 | 面向用户的明确失败原因；不得为空。 | 类型约束见对应对象 |
| `retryable` | [Bool](./Bool.md) | 是 | 是否允许按原契约恢复 | 类型约束见对应对象 |
| `failed_phase` | [NonEmptyText](./NonEmptyText.md) | 是 | 失败阶段 | 类型约束见对应对象 |
| `recover_hint` | [Text](./Text.md) | 否 | 可允许的修复建议 | 类型约束见对应对象 |
| `evidence_refs` | 数组&lt;[Ref](./Ref.md)&gt; | 否 | 受控诊断证据 | 最少项 `0`；最多项 `256` |
| `side_effect_state` | [EffectState](./EffectState.md) | 否 | 实际副作用状态 | 类型约束见对应对象 |
| `retry_after_ms` | [Duration](./Duration.md) | 否 | 可选退避 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "code": "example_001",
  "category": "arguments",
  "message": "example_001",
  "retryable": true,
  "failed_phase": "example_001"
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.Failure`。
