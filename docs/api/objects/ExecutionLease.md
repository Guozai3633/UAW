# ExecutionLease

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：运行与会话。

Run/节点恢复租约归Run，与Agent对话控制租约区分。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `id` | [ID](./ID.md) | 是 | 租约 | 类型约束见对应对象 |
| `run_id` | [ID](./ID.md) | 是 | Run | 类型约束见对应对象 |
| `node_id` | [ID](./ID.md) | 否 | 可选节点 | 类型约束见对应对象 |
| `holder` | [Principal](./Principal.md) | 是 | 当前执行服务/worker | 类型约束见对应对象 |
| `fencing_token` | [Revision](./Revision.md) | 是 | 单调栅栏 | 类型约束见对应对象 |
| `expires_at` | [Timestamp](./Timestamp.md) | 是 | 过期 | 类型约束见对应对象 |
| `revision` | [Revision](./Revision.md) | 是 | 租约修订 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "id": "example_001",
  "run_id": "example_001",
  "holder": {
    "id": "example_001",
    "kind": "user",
    "auth_session_id": "example_001"
  },
  "fencing_token": 0,
  "expires_at": "2026-10-07T02:00:00Z",
  "revision": 0
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.ExecutionLease`。
