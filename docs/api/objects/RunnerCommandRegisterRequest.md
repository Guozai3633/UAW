# RunnerCommandRegisterRequest

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：运行与会话。

仅内部控制服务可创建签字记录，不发送命令。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `command_id` | [ID](./ID.md) | 是 | 稳定命令 | 类型约束见对应对象 |
| `request_ref` | [Ref](./Ref.md) | 是 | 已登记实际请求 | 类型约束见对应对象 |
| `device_ref` | [Ref](./Ref.md) | 是 | 当前设备绑定 | 类型约束见对应对象 |
| `lease_ref` | [Ref](./Ref.md) | 是 | 当前根租约 | 类型约束见对应对象 |
| `fencing_token` | [Revision](./Revision.md) | 是 | 栅栏 | 类型约束见对应对象 |
| `expires_at` | [Timestamp](./Timestamp.md) | 是 | 期限 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "command_id": "example_001",
  "request_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "device_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "lease_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "fencing_token": 0,
  "expires_at": "2026-10-07T02:00:00Z"
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.RunnerCommandRegisterRequest`。
