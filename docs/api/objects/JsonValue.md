# JsonValue

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：公共协议。

仅用于显式扩展载荷/工具动态参数；必须再按关联schema验证，非可信权限。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 类型

互斥选择。—

## oneOf结构规则

```json
{
  "oneOf": [
    {
      "type": "null"
    },
    {
      "type": "boolean"
    },
    {
      "type": "number"
    },
    {
      "type": "string"
    },
    {
      "type": "array",
      "items": {
        "$ref": "#/$defs/JsonValue"
      }
    },
    {
      "type": "object",
      "additionalProperties": {
        "$ref": "#/$defs/JsonValue"
      }
    }
  ]
}
```

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
null
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.JsonValue`。
