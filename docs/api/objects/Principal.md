# Principal

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：公共协议。

可信身份摘要，不包含凭据。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `id` | [ID](./ID.md) | 是 | 身份ID | 类型约束见对应对象 |
| `kind` | enum: `user` / `admin` / `service` / `runner` | 是 | 身份类别 | — |
| `auth_session_id` | [ID](./ID.md) | 是 | 已认证会话/设备绑定 | 类型约束见对应对象 |
| `delegated_by` | [ID](./ID.md) | 否 | 委托来源 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "id": "example_001",
  "kind": "user",
  "auth_session_id": "example_001"
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.Principal`。
