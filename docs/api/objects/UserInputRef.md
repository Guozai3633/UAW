# UserInputRef

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：公共协议。

真实用户输入或已认证用户配置动作的引用；结构限制为input，来源真实性仍由Run核验。

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
          "const": "input"
        }
      }
    }
  ]
}
```

## 运行时约束

- 必须解析到同主体真实用户行为记录；不能引用网页/模型输出授权创建、模型覆盖或审批。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "kind": "input",
  "id": "example_001",
  "version": "example_001"
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.UserInputRef`。
