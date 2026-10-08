# RunnerChannelSnapshot

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：运行与会话。

独立可信通道源读取的当前设备拥有者及认证身份，不接受网络/模型自报。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `device_id` | [ID](./ID.md) | 是 | 设备 | 类型约束见对应对象 |
| `owner` | [Principal](./Principal.md) | 是 | 原用户 | 类型约束见对应对象 |
| `actor` | [Principal](./Principal.md) | 是 | 当前认证Runner | 类型约束见对应对象 |
| `pairing_ref` | [Ref](./Ref.md) | 是 | 实际配对版本 | 类型约束见对应对象 |
| `channel_ref` | [Ref](./Ref.md) | 是 | 实际通道版本 | 类型约束见对应对象 |
| `key_ref` | [Ref](./Ref.md) | 是 | 设备公钥版本 | 类型约束见对应对象 |
| `connected` | [Bool](./Bool.md) | 是 | 实际在线 | 类型约束见对应对象 |
| `expires_at` | [Timestamp](./Timestamp.md) | 是 | 当前通道期限 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "device_id": "example_001",
  "owner": {
    "id": "example_001",
    "kind": "user",
    "auth_session_id": "example_001"
  },
  "actor": {
    "id": "example_001",
    "kind": "user",
    "auth_session_id": "example_001"
  },
  "pairing_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "channel_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "key_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "connected": true,
  "expires_at": "2026-10-07T02:00:00Z"
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.RunnerChannelSnapshot`。
