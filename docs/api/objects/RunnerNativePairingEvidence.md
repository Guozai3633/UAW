# RunnerNativePairingEvidence

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：运行与会话。

独立本机owning Reader返回的确认；不可从HTTP approved生成。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `enrollment_id` | [ID](./ID.md) | 是 | 原登记 | 类型约束见对应对象 |
| `owner` | [Principal](./Principal.md) | 是 | 原完整用户会话 | 类型约束见对应对象 |
| `device_id` | [ID](./ID.md) | 是 | 原设备 | 类型约束见对应对象 |
| `device_identity` | [RunnerProcessIdentity](./RunnerProcessIdentity.md) | 是 | 原OS实例 | 类型约束见对应对象 |
| `proof_document_hash` | [Hash](./Hash.md) | 是 | 双方签署原挑战摘要 | 类型约束见对应对象 |
| `confirmation_ref` | [Ref](./Ref.md) | 是 | 准确本机决定来源 | 类型约束见对应对象 |
| `expires_at` | [Timestamp](./Timestamp.md) | 是 | 实际本机确认期限 | 类型约束见对应对象 |
| `device_proof` | [NonEmptyText](./NonEmptyText.md) | 是 | 原设备签名 | 类型约束见对应对象 |
| `control_proof` | [NonEmptyText](./NonEmptyText.md) | 是 | 原控制签名 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "enrollment_id": "example_001",
  "owner": {
    "id": "example_001",
    "kind": "user",
    "auth_session_id": "example_001"
  },
  "device_id": "example_001",
  "device_identity": {
    "pid": 1,
    "created": "133987654321098765",
    "user_sid": "example_001",
    "logon_sid": "example_001"
  },
  "proof_document_hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "confirmation_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "expires_at": "2026-10-07T02:00:00Z",
  "device_proof": "example_001",
  "control_proof": "example_001"
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.RunnerNativePairingEvidence`。
