# CapabilityRequirements

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：模型调用。

本次调用需要的模型能力。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `tool_calling` | [Bool](./Bool.md) | 是 | 工具协议 | 类型约束见对应对象 |
| `structured_output` | [Bool](./Bool.md) | 是 | 结构化结果 | 类型约束见对应对象 |
| `vision` | [Bool](./Bool.md) | 是 | 图像输入 | 类型约束见对应对象 |
| `minimum_context_tokens` | [Count](./Count.md) | 是 | 最小上下文 | 类型约束见对应对象 |
| `minimum_output_tokens` | [Count](./Count.md) | 是 | 最小输出 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "tool_calling": true,
  "structured_output": true,
  "vision": true,
  "minimum_context_tokens": 0,
  "minimum_output_tokens": 0
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.CapabilityRequirements`。
