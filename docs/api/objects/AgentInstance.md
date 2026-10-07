# AgentInstance

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：Agent执行与协作。

运行实例与持久定义分离。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `id` | [ID](./ID.md) | 是 | 实例ID | 类型约束见对应对象 |
| `run_id` | [ID](./ID.md) | 是 | 所属运行 | 类型约束见对应对象 |
| `parent_agent_ref` | [Ref](./Ref.md) | 否 | 根实例无父 | 类型约束见对应对象 |
| `definition_ref` | [Ref](./Ref.md) | 否 | 使用的角色版本 | 类型约束见对应对象 |
| `delegation_ref` | [Ref](./Ref.md) | 否 | 子实例的委派契约 | 类型约束见对应对象 |
| `status` | [State](./State.md) | 是 | 实例状态 | 类型约束见对应对象 |
| `model_policy_ref` | [Ref](./Ref.md) | 是 | 实际继承或覆盖政策 | 类型约束见对应对象 |
| `capability_policy_ref` | [Ref](./Ref.md) | 是 | 有效权限交集 | 类型约束见对应对象 |
| `context_epoch` | [Revision](./Revision.md) | 是 | 上下文纪元 | 类型约束见对应对象 |
| `workspace_ref` | [Ref](./Ref.md) | 否 | 需要文件操作时绑定 | 类型约束见对应对象 |
| `result_ref` | [Ref](./Ref.md) | 否 | 终态结果 | 类型约束见对应对象 |
| `revision` | [Revision](./Revision.md) | 是 | 实例版本 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "id": "example_001",
  "run_id": "example_001",
  "status": "pending",
  "model_policy_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "capability_policy_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "context_epoch": 0,
  "revision": 0
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.AgentInstance`。
