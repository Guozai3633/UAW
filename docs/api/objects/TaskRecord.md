# TaskRecord

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：运行与会话。

跨会话关联任务需显式绑定和版本冲突处理。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `id` | [ID](./ID.md) | 是 | 任务 | 类型约束见对应对象 |
| `revision` | [Revision](./Revision.md) | 是 | 目标版本 | 类型约束见对应对象 |
| `conversation_refs` | 数组&lt;[Ref](./Ref.md)&gt; | 是 | 关联会话 | 最少项 `0`；最多项 `256` |
| `frame_ref` | [Ref](./Ref.md) | 否 | 正式理解 | 类型约束见对应对象 |
| `active_run_refs` | 数组&lt;[Ref](./Ref.md)&gt; | 是 | 运行 | 最少项 `0`；最多项 `256` |
| `artifact_refs` | 数组&lt;[Ref](./Ref.md)&gt; | 是 | 成果 | 最少项 `0`；最多项 `256` |
| `created_at` | [Timestamp](./Timestamp.md) | 是 | 创建时间 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "id": "example_001",
  "revision": 0,
  "conversation_refs": [],
  "active_run_refs": [],
  "artifact_refs": [],
  "created_at": "2026-10-07T02:00:00Z"
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.TaskRecord`。
