# RecoveryDecision

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：公共协议。

恢复建议不是任意换模型/工具的许可。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `action` | [RecoveryAction](./RecoveryAction.md) | 是 | 可执行恢复 | 类型约束见对应对象 |
| `retry_after_ms` | [Duration](./Duration.md) | 否 | 等待 | 类型约束见对应对象 |
| `replacement_ref` | [Ref](./Ref.md) | 否 | 仅已授权等价提供方/Auto模型 | 类型约束见对应对象 |
| `reason` | [NonEmptyText](./NonEmptyText.md) | 是 | 依据 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "action": "retry",
  "reason": "example_001"
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.RecoveryDecision`。
