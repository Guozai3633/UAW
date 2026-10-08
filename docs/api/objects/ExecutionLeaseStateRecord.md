# ExecutionLeaseStateRecord

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：运行与会话。

同Run根执行租约的当前持久状态，终态不因时钟回退复活。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `lease` | [ExecutionLease](./ExecutionLease.md) | 是 | 当前租约 | 类型约束见对应对象 |
| `state` | [ExecutionLeaseState](./ExecutionLeaseState.md) | 是 | 状态 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 运行时约束

- 行revision等于lease.revision；新接管递增fencing_token，续约不改变fence；不授予工具/文件/设备权限。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "lease": {
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
  },
  "state": "active"
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.ExecutionLeaseStateRecord`。
