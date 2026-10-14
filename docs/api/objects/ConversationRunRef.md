# ConversationRunRef

状态：对象契约0.2 / conversation-v1；可用范围见具体接口与实施记录。所属：运行与会话。



[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 类型

见结构规则。—

## allOf结构规则

```json
{
  "allOf": [
    {
      "$ref": "#/$defs/Ref"
    },
    {
      "properties": {
        "kind": {
          "const": "run"
        }
      }
    }
  ]
}
```

## 运行时约束

- 结构限定来源类型；真实主体、当前权限、版本仍由来源域核验。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "kind": "run",
  "id": "example_001",
  "version": "example_001"
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.ConversationRunRef`。
