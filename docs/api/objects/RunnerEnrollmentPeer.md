# RunnerEnrollmentPeer

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：运行与会话。

独立控制源捕获的候选进程与角色key。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `identity` | [RunnerProcessIdentity](./RunnerProcessIdentity.md) | 是 | 独立OS观察 | 类型约束见对应对象 |
| `actor` | [Principal](./Principal.md) | 是 | 精确角色主体 | 类型约束见对应对象 |
| `role` | enum: `control` / `device` | 是 | 签名角色 | — |
| `key_id` | [ID](./ID.md) | 是 | 原key身份 | 类型约束见对应对象 |
| `key_ref` | [Ref](./Ref.md) | 是 | 原key版本与摘要 | 类型约束见对应对象 |
| `public_key` | string | 是 | 32字节Ed25519公钥标准base64；不是私钥 | 最少字符 `44`；最多字符 `44`；正则 `^[A-Za-z0-9+/]{43}=$` |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
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
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.RunnerEnrollmentPeer`。
