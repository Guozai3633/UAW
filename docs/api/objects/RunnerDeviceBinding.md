# RunnerDeviceBinding

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：运行与会话。

平台拥有的设备/通道归属，撤销与到期不自动复活。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `device_id` | [ID](./ID.md) | 是 | 设备 | 类型约束见对应对象 |
| `revision` | [Revision](./Revision.md) | 是 | CAS | 类型约束见对应对象 |
| `source` | [RunnerChannelSnapshot](./RunnerChannelSnapshot.md) | 是 | 登记时实际来源 | 类型约束见对应对象 |
| `state` | [RunnerBindingState](./RunnerBindingState.md) | 是 | 当前状态 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "device_id": "example_001",
  "revision": 0,
  "source": {
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
  },
  "state": "active"
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.RunnerDeviceBinding`。
