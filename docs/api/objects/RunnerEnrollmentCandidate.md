# RunnerEnrollmentCandidate

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：运行与会话。

独立来源候选；不授予配对或文件权限。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `id` | [ID](./ID.md) | 是 | 候选身份 | 类型约束见对应对象 |
| `owner` | [Principal](./Principal.md) | 是 | 实际当前Web用户完整身份 | 类型约束见对应对象 |
| `device_id` | [ID](./ID.md) | 是 | 独立设备身份 | 类型约束见对应对象 |
| `control` | [RunnerEnrollmentPeer](./RunnerEnrollmentPeer.md) | 是 | 控制进程 | 类型约束见对应对象 |
| `device` | [RunnerEnrollmentPeer](./RunnerEnrollmentPeer.md) | 是 | 设备进程 | 类型约束见对应对象 |
| `expires_at` | [Timestamp](./Timestamp.md) | 是 | 候选期限 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "id": "example_001",
  "owner": {
    "id": "example_001",
    "kind": "user",
    "auth_session_id": "example_001"
  },
  "device_id": "example_001",
  "control": {
    "identity": {
      "pid": 1,
      "created": "133987654321098765",
      "user_sid": "example_001",
      "logon_sid": "example_001"
    },
    "actor": {
      "id": "example_001",
      "kind": "user",
      "auth_session_id": "example_001"
    },
    "role": "control",
    "key_id": "example_001",
    "key_ref": {
      "kind": "web",
      "id": "example_001",
      "version": "example_001"
    },
    "public_key": "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA="
  },
  "device": {
    "identity": {
      "pid": 1,
      "created": "133987654321098765",
      "user_sid": "example_001",
      "logon_sid": "example_001"
    },
    "actor": {
      "id": "example_001",
      "kind": "user",
      "auth_session_id": "example_001"
    },
    "role": "control",
    "key_id": "example_001",
    "key_ref": {
      "kind": "web",
      "id": "example_001",
      "version": "example_001"
    },
    "public_key": "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA="
  },
  "expires_at": "2026-10-07T02:00:00Z"
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.RunnerEnrollmentCandidate`。
