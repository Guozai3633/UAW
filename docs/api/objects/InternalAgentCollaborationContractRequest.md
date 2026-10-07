# InternalAgentCollaborationContractRequest

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：Agent执行与协作。

子任务契约的私有阶段输入。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `parent_goal_ref` | [Ref](./Ref.md) | 是 | 父当前理解/要求版本，防止子目标偏离。 | 类型约束见对应对象 |
| `proposed_goal` | [Text](./Text.md) | 是 | 父Agent拟定的有界子目标，待委派契约核对。 | 类型约束见对应对象 |
| `input_refs` | 数组&lt;[Ref](./Ref.md)&gt; | 是 | 授权并固定实际版本的输入集合。 | 最多项 `256` |
| `output_contract` | [Contract](./Contract.md) | 是 | 本分工的目标、必须成果和真实证据标准。 | 类型约束见对应对象 |
| `budget` | [Budget](./Budget.md) | 是 | 任务/分工资源上限，不能超过父预留。 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 运行时约束

- DelegationSpec固定task/plan与输入版本。
- 服务端注入可信上下文，不通过HTTP或LLM工具直接访问。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "parent_goal_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "proposed_goal": "example_001",
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
  }
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.InternalAgentCollaborationContractRequest`。
