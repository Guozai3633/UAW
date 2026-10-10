# WebLaunchTicket

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：运行与会话。

内部持久身份记录，不含原bearer、启动code、cookie或CSRF。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `id` | [ID](./ID.md) | 是 | 随机记录身份 | 类型约束见对应对象 |
| `principal` | [Principal](./Principal.md) | 是 | 独立认证用户 | 类型约束见对应对象 |
| `origin` | [URL](./URL.md) | 是 | 精确Web origin | 类型约束见对应对象 |
| `credential_epoch` | [Hash](./Hash.md) | 是 | 当前账号凭据纪元 | 类型约束见对应对象 |
| `expires_at` | [Timestamp](./Timestamp.md) | 是 | 有界期限 | 类型约束见对应对象 |
| `state` | enum: `issued` / `consumed` | 是 | 当前状态 | — |
| `revision` | [Revision](./Revision.md) | 是 | 持久CAS版本 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "id": "example_001",
  "principal": {
    "id": "example_001",
    "kind": "user",
    "auth_session_id": "example_001"
  },
  "origin": "https://example.org/resource",
  "credential_epoch": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "expires_at": "2026-10-07T02:00:00Z",
  "state": "issued",
  "revision": 0
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.WebLaunchTicket`。
