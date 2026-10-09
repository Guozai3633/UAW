# AgentLoopState

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：Agent执行与协作。

自有CAS状态；框架检查点不替代此权威。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `instance_id` | [ID](./ID.md) | 是 | 根实例 | 类型约束见对应对象 |
| `revision` | [Revision](./Revision.md) | 是 | CAS | 类型约束见对应对象 |
| `steps` | [Revision](./Revision.md) | 是 | 已认领模型步骤 | 类型约束见对应对象 |
| `frame_ref` | [Ref](./Ref.md) | 是 | 当前任务理解 | 类型约束见对应对象 |
| `observation_refs` | 数组&lt;[Ref](./Ref.md)&gt; | 是 | 已登记观察 | 最少项 `0`；最多项 `256` |
| `active_operation_ref` | [Ref](./Ref.md) | 否 | 原步骤持久意图 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 运行时约束

- 仅可信内部适配器写入，当前拥有者/session/Run/固定模型/角色和资源逐次复查。
- 不证明框架END、模型建议或传输成功已经完成用户任务。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "instance_id": "example_001",
  "revision": 0,
  "steps": 0,
  "frame_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "observation_refs": []
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.AgentLoopState`。
