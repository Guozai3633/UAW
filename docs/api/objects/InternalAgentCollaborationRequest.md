# InternalAgentCollaborationRequest

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：Agent执行与协作。

互斥分支；所有字段须匹配所选action。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 类型

互斥选择。—

## oneOf结构规则

```json
{
  "oneOf": [
    {
      "$ref": "#/$defs/InternalAgentCollaborationRequestDelegate"
    },
    {
      "$ref": "#/$defs/InternalAgentCollaborationRequestJoin"
    },
    {
      "$ref": "#/$defs/InternalAgentCollaborationRequestHandoff"
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
  "action": "delegate",
  "parameters": {
    "goal": "example_001",
    "input_refs": [],
    "output_contract": {
      "goal": "example_001",
      "requirements": [],
      "outputs": [],
      "version": "example_001"
    },
    "budget": {
      "limits": {
        "input_tokens": 0,
        "output_tokens": 0,
        "model_calls": 0,
        "tool_calls": 0,
        "child_agents": 0,
        "wall_time_ms": 0,
        "money": "0",
        "currency": "CNY"
      },
      "max_steps": 0,
      "max_depth": 0,
      "deadline": "2026-10-07T02:00:00Z"
    },
    "read_refs": [],
    "write_refs": [],
    "creation_key": "example_001"
  }
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.InternalAgentCollaborationRequest`。
