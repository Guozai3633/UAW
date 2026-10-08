# MeasuredResources

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：运行与会话。

已观察用量；pending时所有未知维度均省略，币种必需，不能用0代替未知。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `input_tokens` | [Count](./Count.md) | 否 | 输入token | 类型约束见对应对象 |
| `output_tokens` | [Count](./Count.md) | 否 | 输出token | 类型约束见对应对象 |
| `model_calls` | [Count](./Count.md) | 否 | 模型调用 | 类型约束见对应对象 |
| `tool_calls` | [Count](./Count.md) | 否 | 工具调用 | 类型约束见对应对象 |
| `child_agents` | [Count](./Count.md) | 否 | 子实例数 | 类型约束见对应对象 |
| `wall_time_ms` | [Duration](./Duration.md) | 否 | 任务墙钟时间 | 类型约束见对应对象 |
| `money` | [Decimal](./Decimal.md) | 否 | 金额 | 类型约束见对应对象 |
| `currency` | string | 是 | 币种 | 正则 `^[A-Z]{3}$` |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 运行时约束

- 缺失项维持预留；确认账单前不能释放未知消耗。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "currency": "CNY"
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.MeasuredResources`。
