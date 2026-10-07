# InternalToolMcpOutput

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：工具运行。

互斥分支；所有字段须匹配所选action。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 类型

互斥选择。—

## oneOf结构规则

```json
{
  "oneOf": [
    {
      "$ref": "#/$defs/InternalToolMcpOutputConnect"
    },
    {
      "$ref": "#/$defs/InternalToolMcpOutputDiscover"
    },
    {
      "$ref": "#/$defs/InternalToolMcpOutputCall"
    },
    {
      "$ref": "#/$defs/InternalToolMcpOutputClose"
    }
  ]
}
```

## 运行时约束

- 禁止用一个动作的参数调用另一个动作；服务端先确定action再校验分支。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "action": "connect",
  "result": {
    "id": "example_001",
    "provider_ref": {
      "kind": "web",
      "id": "example_001",
      "version": "example_001"
    },
    "state": "disconnected",
    "capability_revision": 0
  }
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.InternalToolMcpOutput`。
