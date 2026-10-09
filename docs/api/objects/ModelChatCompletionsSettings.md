# ModelChatCompletionsSettings

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：配置与共享基础设施。

显式Chat Completions协议；预留金额不是价格或实际账单。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `model_name` | [NonEmptyText](./NonEmptyText.md) | 是 | 固定供应商模型 | 类型约束见对应对象 |
| `timeout_ms` | [Duration](./Duration.md) | 是 | 总调用上限 | ≥ `1000`；≤ `300000`；类型约束见对应对象 |
| `output_token_parameter` | [NonEmptyText](./NonEmptyText.md) | 是 | 供应商输出额度字段 | 类型约束见对应对象 |
| `reservation_money` | [Decimal](./Decimal.md) | 是 | 每attempt的管理员预留额度 | 类型约束见对应对象 |
| `allow_temperature` | [Bool](./Bool.md) | 是 | 是否支持temperature | 类型约束见对应对象 |
| `allowed_response_models` | 数组&lt;[NonEmptyText](./NonEmptyText.md)&gt; | 否 | 批准的同模型响应别名 | 最少项 `0`；最多项 `256` |
| `reasoning_levels` | 数组&lt;[NonEmptyText](./NonEmptyText.md)&gt; | 否 | 批准的推理档位 | 最少项 `0`；最多项 `256` |
| `structured_output_mode` | [NonEmptyText](./NonEmptyText.md) | 否 | json_schema原生严格模式或json_object加UAW本地schema校验；默认原生模式，不自动降级 | 类型约束见对应对象 |
| `include_n` | [Bool](./Bool.md) | 否 | 是否发送n=1；省略时保留旧行为 | 类型约束见对应对象 |
| `default_reasoning_level` | [NonEmptyText](./NonEmptyText.md) | 否 | 管理员批准的默认推理档位，必须属于reasoning_levels，记入实际配置 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "model_name": "example_001",
  "timeout_ms": 1000,
  "output_token_parameter": "max_completion_tokens",
  "reservation_money": "0",
  "allow_temperature": true
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.ModelChatCompletionsSettings`。
