# InternalToolInvocationDispatchRequest

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：工具运行。

意图登记与执行的私有阶段输入。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `validated_action_ref` | [Ref](./Ref.md) | 是 | 已经schema/precheck/recheck的固定动作。 | 类型约束见对应对象 |
| `reservation_ref` | [Ref](./Ref.md) | 是 | 父账本内已预留资源，派发前必须有效。 | 类型约束见对应对象 |
| `business_key` | [Text](./Text.md) | 否 | 提供方认可的逻辑幂等键；重试沿用。 | 类型约束见对应对象 |
| `provider_binding_ref` | [Ref](./Ref.md) | 是 | 有效提供方配置与账号授权的固定绑定。 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 运行时约束

- 先意图后发送；attempt关联稳定action ID。
- 服务端注入可信上下文，不通过HTTP或LLM工具直接访问。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "validated_action_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "reservation_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "provider_binding_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  }
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.InternalToolInvocationDispatchRequest`。
