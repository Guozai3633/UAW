# InternalToolMcpInvokeRequest

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：工具运行。

闸门后调用的私有阶段输入。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `validated_call_ref` | [Ref](./Ref.md) | 是 | 已规范化、已授权调用记录及版本。 | 类型约束见对应对象 |
| `session_ref` | [Ref](./Ref.md) | 是 | 当前active的MCP连接session及能力修订。 | 类型约束见对应对象 |
| `business_key` | [Text](./Text.md) | 否 | 提供方认可的逻辑幂等键；重试沿用。 | 类型约束见对应对象 |
| `attempt_id` | [ID](./ID.md) | 是 | 实际执行尝试；每次重试不同，与稳定action_id分开。 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 运行时约束

- 不在MCP层另批准一份动作，使用原action/attempt关联。
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
  "session_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "attempt_id": "example_001"
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.InternalToolMcpInvokeRequest`。
