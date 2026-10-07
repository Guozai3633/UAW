# ModelCapabilityRequest

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：模型调用。

当前模型能力核对与Auto候选选择共用明确请求。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `policy_ref` | [Ref](./Ref.md) | 是 | 授权政策 | 类型约束见对应对象 |
| `requirements` | [CapabilityRequirements](./CapabilityRequirements.md) | 是 | 能力 | 类型约束见对应对象 |
| `context_tokens` | [Count](./Count.md) | 是 | 输入 | 类型约束见对应对象 |
| `budget_ref` | [Ref](./Ref.md) | 是 | 预留 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "policy_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "requirements": {
    "tool_calling": true,
    "structured_output": true,
    "vision": true,
    "minimum_context_tokens": 0,
    "minimum_output_tokens": 0
  },
  "context_tokens": 0,
  "budget_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  }
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.ModelCapabilityRequest`。
