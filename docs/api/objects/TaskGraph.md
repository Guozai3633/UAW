# TaskGraph

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：Agent执行与协作。

图修订不可变，执行状态另存。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `task_id` | [ID](./ID.md) | 是 | 所属任务 | 类型约束见对应对象 |
| `revision` | [Revision](./Revision.md) | 是 | 计划版本 | 类型约束见对应对象 |
| `planning` | enum: `steps` / `dag` | 是 | 图仅用于步骤清单或DAG。 | — |
| `nodes` | 数组&lt;[NodeSpec](./NodeSpec.md)&gt; | 是 | 完整节点集合 | 最少项 `0`；最多项 `256` |
| `source_frame_ref` | [Ref](./Ref.md) | 是 | 目标理解版本 | 类型约束见对应对象 |
| `created_at` | [Timestamp](./Timestamp.md) | 是 | 提交时间 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "task_id": "example_001",
  "revision": 0,
  "planning": "steps",
  "nodes": [],
  "source_frame_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "created_at": "2026-10-07T02:00:00Z"
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.TaskGraph`。
