# WebSession

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：运行与会话。

浏览器用户身份和CSRF；会话凭据只在HttpOnly cookie中。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `principal` | [Principal](./Principal.md) | 是 | 服务器签发的用户和Web session | 类型约束见对应对象 |
| `expires_at` | [Timestamp](./Timestamp.md) | 是 | 固定会话截止 | 类型约束见对应对象 |
| `csrf_token` | [Hash](./Hash.md) | 是 | 内存保留，修改请求X-UAW-CSRF | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "principal": {
    "id": "example_001",
    "kind": "user",
    "auth_session_id": "example_001"
  },
  "expires_at": "2026-10-07T02:00:00Z",
  "csrf_token": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.WebSession`。
