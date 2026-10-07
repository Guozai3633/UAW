# InternalAgentSchedulerRequest

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：Agent执行与协作。

节点与资源调度的私有阶段输入。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `plan_ref` | [Ref](./Ref.md) | 是 | 已校验、已提交的计划修订，不是未接受建议。 | 类型约束见对应对象 |
| `node_states` | 映射&lt;string, [State](./State.md)&gt; | 是 | 当前计划版本每个节点的执行状态。 | 最多键 `256`；值逐项按schema校验 |
| `available_resources` | [ResourceSnapshot](./ResourceSnapshot.md) | 是 | 当前可用资源快照；实际调度仍原子预留。 | 类型约束见对应对象 |
| `expected_revision` | [Revision](./Revision.md) | 是 | 目标域CAS版本；不匹配返回conflict并重新读取。 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 运行时约束

- 领用与预留使用一致提交或可恢复分配意图；完成提交携带node attempt和lease版本。
- 服务端注入可信上下文，不通过HTTP或LLM工具直接访问。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "plan_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "node_states": {},
  "available_resources": {
    "revision": 0,
    "available": {
      "input_tokens": 0,
      "output_tokens": 0,
      "model_calls": 0,
      "tool_calls": 0,
      "child_agents": 0,
      "wall_time_ms": 0,
      "money": "0",
      "currency": "CNY"
    },
    "active_leases": []
  },
  "expected_revision": 0
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.InternalAgentSchedulerRequest`。
