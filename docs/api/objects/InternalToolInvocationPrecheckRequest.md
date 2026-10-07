# InternalToolInvocationPrecheckRequest

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：工具运行。

执行预检的私有阶段输入。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `validated_call_ref` | [Ref](./Ref.md) | 是 | 已规范化、已授权调用记录及版本。 | 类型约束见对应对象 |
| `effective_policy_ref` | [Ref](./Ref.md) | 是 | 当前有效权限/旗标/审批政策版本。 | 类型约束见对应对象 |
| `budget_estimate` | [ResourceVector](./ResourceVector.md) | 是 | 派发前估算的资源，失败尝试也进入结算。 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 运行时约束

- PrecheckDecision短时记录不是永久授权。
- 服务端注入可信上下文，不通过HTTP或LLM工具直接访问。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "validated_call_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "effective_policy_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "budget_estimate": {
    "input_tokens": 0,
    "output_tokens": 0,
    "model_calls": 0,
    "tool_calls": 0,
    "child_agents": 0,
    "wall_time_ms": 0,
    "money": "0",
    "currency": "CNY"
  }
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.InternalToolInvocationPrecheckRequest`。
