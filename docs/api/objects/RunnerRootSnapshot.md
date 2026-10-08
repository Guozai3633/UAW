# RunnerRootSnapshot

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：运行与会话。

真实授权根来源的当前opaque元数据，不包含本机路径。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `owner` | [Principal](./Principal.md) | 是 | 原用户 | 类型约束见对应对象 |
| `device_id` | [ID](./ID.md) | 是 | 设备 | 类型约束见对应对象 |
| `workspace_ref` | [Ref](./Ref.md) | 是 | 实际工作区 | 类型约束见对应对象 |
| `root_handle` | [ID](./ID.md) | 是 | 授权根 | 类型约束见对应对象 |
| `binding_revision` | [Revision](./Revision.md) | 是 | 根版本 | 类型约束见对应对象 |
| `allowed_actions` | 数组&lt;[ID](./ID.md)&gt; | 是 | 当前获准读动作 | 最少项 `0`；最多项 `256` |
| `expires_at` | [Timestamp](./Timestamp.md) | 是 | 根期限 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "owner": {
    "id": "example_001",
    "kind": "user",
    "auth_session_id": "example_001"
  },
  "device_id": "example_001",
  "workspace_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "root_handle": "example_001",
  "binding_revision": 0,
  "allowed_actions": [],
  "expires_at": "2026-10-07T02:00:00Z"
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.RunnerRootSnapshot`。
