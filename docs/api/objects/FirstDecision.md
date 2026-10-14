# FirstDecision

状态：对象契约0.2 / conversation-v1；可用范围见具体接口与实施记录。所属：Agent执行与协作。

首次模型输出；精确互斥分支，不接收真实模型/主体/授权元数据。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 类型

互斥选择。—

## oneOf结构规则

```json
{
  "oneOf": [
    {
      "$ref": "#/$defs/FirstReplyDecision"
    },
    {
      "$ref": "#/$defs/FirstToolDecision"
    },
    {
      "$ref": "#/$defs/FirstAskDecision"
    },
    {
      "$ref": "#/$defs/FirstDeliverDecision"
    }
  ]
}
```

## 运行时约束

- 模型提案不直接结束Run；权限和来源由Runtime核验。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "protocol": "conversation-v1",
  "action": "reply",
  "text": "example_001"
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.FirstDecision`。
