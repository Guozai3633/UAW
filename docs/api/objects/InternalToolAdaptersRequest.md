# InternalToolAdaptersRequest

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：工具运行。

领域与外部适配器的私有阶段输入。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `provider_kind` | enum: `local` / `runtime` / `mcp` / `api` | 是 | 内部、本地、MCP或API适配通道。 | — |
| `validated_call` | [Ref](./Ref.md) | 是 | 已经经过闸门且参数Hash固定的工具调用。 | 类型约束见对应对象 |
| `deadline` | [Timestamp](./Timestamp.md) | 是 | 绝对UTC截止；重试和子调用不能延长父deadline。 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 运行时约束

- 适配器不拥有目标Runtime业务状态，只持调用/协议关联引用。
- 服务端注入可信上下文，不通过HTTP或LLM工具直接访问。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "provider_kind": "local",
  "validated_call": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "deadline": "2026-10-07T02:00:00Z"
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.InternalToolAdaptersRequest`。
