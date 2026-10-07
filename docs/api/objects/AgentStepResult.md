# AgentStepResult

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：Agent执行与协作。

每步建议下一动作，由硬闸门确认。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `action` | [AgentStepAction](./AgentStepAction.md) | 是 | 下一动作 | 类型约束见对应对象 |
| `model_output_ref` | [Ref](./Ref.md) | 是 | 模型依据 | 类型约束见对应对象 |
| `proposed_calls` | 数组&lt;[ToolCall](./ToolCall.md)&gt; | 是 | 工具建议 | 最少项 `0`；最多项 `256` |
| `completion_proposal_ref` | [Ref](./Ref.md) | 否 | 完成提案 | 类型约束见对应对象 |
| `instance_ref` | [Ref](./Ref.md) | 是 | 提交后实例 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "action": "respond",
  "model_output_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "proposed_calls": [],
  "instance_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  }
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.AgentStepResult`。
