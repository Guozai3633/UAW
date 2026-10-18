# QualityUsage

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：配置与共享基础设施。



[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `input_tokens` | 至少一个分支 | 是 | 见类型说明 | — |
| `output_tokens` | 至少一个分支 | 是 | 见类型说明 | — |
| `model_calls` | 至少一个分支 | 是 | 见类型说明 | — |
| `tool_calls` | 至少一个分支 | 是 | 见类型说明 | — |
| `money` | 至少一个分支 | 是 | 见类型说明 | — |
| `currency` | string | 是 | 见类型说明 | 正则 `^[A-Z]{3}$` |
| `billing_state` | enum: `confirmed` / `pending` / `unknown` | 是 | 见类型说明 | — |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 运行时约束

- 原来源/回答版本绑定；认证用户独立判断，未知不当作通过。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "input_tokens": 0,
  "output_tokens": 0,
  "model_calls": 0,
  "tool_calls": 0,
  "money": "0",
  "currency": "CNY",
  "billing_state": "confirmed"
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.QualityUsage`。
