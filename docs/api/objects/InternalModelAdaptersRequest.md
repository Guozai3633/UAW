# InternalModelAdaptersRequest

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：模型调用。

供应商协议适配的私有阶段输入。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `provider_ref` | [Ref](./Ref.md) | 是 | 管理员配置且当前可用的固定提供方版本。 | 类型约束见对应对象 |
| `resolved_model_id` | [ID](./ID.md) | 是 | 在用户固定政策或Auto授权内解析的实际目录ID。 | 类型约束见对应对象 |
| `messages` | 数组&lt;[Message](./Message.md)&gt; | 是 | 按顺序发送给提供方的有来源消息块。 | 最多项 `256` |
| `tools` | 数组&lt;[Schema](./Schema.md)&gt; | 是 | 本次实际暴露给模型的工具参数schema，按稳定版本排序。 | 最多项 `256` |
| `reasoning_config` | [ReasoningConfiguration](./ReasoningConfiguration.md) | 否 | 支持的推理配置，不接受任意Object或用户模型替换。 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 运行时约束

- adapter协议版本固定，供应商响应标识用于对账；不伪造统一能力。
- 服务端注入可信上下文，不通过HTTP或LLM工具直接访问。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "provider_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "resolved_model_id": "example_001",
  "messages": [],
  "tools": []
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.InternalModelAdaptersRequest`。
