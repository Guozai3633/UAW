# InternalWorkspaceBindingOutput

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：工作区与交付。

互斥分支；所有字段须匹配所选action。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 类型

互斥选择。—

## oneOf结构规则

```json
{
  "oneOf": [
    {
      "$ref": "#/$defs/InternalWorkspaceBindingOutputBind"
    },
    {
      "$ref": "#/$defs/InternalWorkspaceBindingOutputCheckScope"
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
  "action": "bind",
  "result": {
    "id": "example_001",
    "revision": 0,
    "device_id": "example_001",
    "display_name": "example_001",
    "root_handle": "example_001",
    "capabilities": [],
    "state": "disconnected"
  }
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.InternalWorkspaceBindingOutput`。
