# NodeSpec

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：Agent执行与协作。

任务图节点，与Agent实例不是一一对应。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `id` | [ID](./ID.md) | 是 | 图内稳定ID | 类型约束见对应对象 |
| `goal` | [NonEmptyText](./NonEmptyText.md) | 是 | 节点目标 | 类型约束见对应对象 |
| `depends_on` | 数组&lt;[ID](./ID.md)&gt; | 是 | 前置节点ID | 最少项 `0`；最多项 `256` |
| `input_refs` | 数组&lt;[Ref](./Ref.md)&gt; | 是 | 固定输入 | 最少项 `0`；最多项 `256` |
| `output_contract` | [Contract](./Contract.md) | 是 | 节点交付标准 | 类型约束见对应对象 |
| `agent_definition_ref` | [Ref](./Ref.md) | 否 | 可选指定角色 | 类型约束见对应对象 |
| `read_refs` | 数组&lt;[Ref](./Ref.md)&gt; | 是 | 预计读集 | 最少项 `0`；最多项 `256` |
| `write_refs` | 数组&lt;[Ref](./Ref.md)&gt; | 是 | 预计写集 | 最少项 `0`；最多项 `256` |
| `budget` | [Budget](./Budget.md) | 是 | 节点预算上限 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 运行时约束

- 依赖必须存在、无自环、无环；并发写必须隔离或串行；图节点不自动创建子Agent。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "id": "example_001",
  "goal": "example_001",
  "depends_on": [],
  "input_refs": [],
  "output_contract": {
    "goal": "example_001",
    "requirements": [],
    "outputs": [],
    "version": "example_001"
  },
  "read_refs": [],
  "write_refs": [],
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

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.NodeSpec`。
