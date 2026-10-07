# NodeState

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：Agent执行与协作。

节点状态与依赖版本。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `node_id` | [ID](./ID.md) | 是 | 节点 | 类型约束见对应对象 |
| `plan_revision` | [Revision](./Revision.md) | 是 | 所属图 | 类型约束见对应对象 |
| `state` | [State](./State.md) | 是 | 执行状态 | 类型约束见对应对象 |
| `input_refs` | 数组&lt;[Ref](./Ref.md)&gt; | 是 | 实际输入 | 最少项 `0`；最多项 `256` |
| `result_refs` | 数组&lt;[Ref](./Ref.md)&gt; | 是 | 结果引用 | 最少项 `0`；最多项 `256` |
| `agent_instance_ref` | [Ref](./Ref.md) | 否 | 执行实例 | 类型约束见对应对象 |
| `failure` | [Failure](./Failure.md) | 否 | 失败详情 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "node_id": "example_001",
  "plan_revision": 0,
  "state": "pending",
  "input_refs": [],
  "result_refs": []
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.NodeState`。
