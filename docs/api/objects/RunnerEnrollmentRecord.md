# RunnerEnrollmentRecord

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：运行与会话。

平台持久的首次设备登记状态；active仍不含目录授权。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `id` | [ID](./ID.md) | 是 | 原操作 | 类型约束见对应对象 |
| `revision` | [Revision](./Revision.md) | 是 | CAS版本 | 类型约束见对应对象 |
| `state` | enum: `pending` / `active` / `revoked` / `expired` | 是 | 登记状态 | — |
| `proof_document` | [RunnerEnrollmentProofDocument](./RunnerEnrollmentProofDocument.md) | 是 | 固定原挑战 | 类型约束见对应对象 |
| `created_at` | [Timestamp](./Timestamp.md) | 是 | 登记时间 | 类型约束见对应对象 |
| `confirmation_ref` | [Ref](./Ref.md) | 否 | 独立本机决定记录 | 类型约束见对应对象 |
| `pairing_ref` | [Ref](./Ref.md) | 否 | 正式完整登记的固定摘要 | 类型约束见对应对象 |
| `device_proof` | string | 否 | 原设备持有签名 | 最少字符 `1`；最多字符 `240` |
| `control_proof` | string | 否 | 原控制持有签名 | 最少字符 `1`；最多字符 `240` |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "id": "example_001",
  "revision": 0,
  "state": "pending",
  "proof_document": {
    "protocol": "uaw-enrollment-v1",
    "enrollment_id": "example_001",
    "candidate_ref": {
      "kind": "web",
      "id": "example_001",
      "version": "example_001"
    },
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
    "nonce": "example_001xxxxxxxxxxxxxxxxxxxxx",
    "expires_at": "2026-10-07T02:00:00Z"
  },
  "created_at": "2026-10-07T02:00:00Z"
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.RunnerEnrollmentRecord`。
