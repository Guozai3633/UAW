# PolicyPayload

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：配置与共享基础设施。

政策按类型分别验证，不使用任意configuration_patch。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 类型

互斥选择。—

## oneOf结构规则

```json
{
  "oneOf": [
    {
      "$ref": "#/$defs/CapabilityPolicy"
    },
    {
      "$ref": "#/$defs/ApprovalPolicy"
    },
    {
      "$ref": "#/$defs/CachePolicy"
    },
    {
      "$ref": "#/$defs/StoragePolicy"
    },
    {
      "$ref": "#/$defs/RetryPolicy"
    }
  ]
}
```

## 运行时约束

- 平台登记后重新分配修订；有效权限仍受用户/本机批准约束。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "id": "example_001",
  "revision": 0,
  "allowed_capabilities": [],
  "denied_capabilities": [],
  "resource_scope": {
    "conversation_id": "example_001"
  },
  "network_allowlist": [],
  "feature_flag_refs": []
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.PolicyPayload`。
