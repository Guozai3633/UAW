# AdminSecretsPutRequest

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：配置与共享基础设施。

仅管理端TLS写入秘密，不回显不记录正文。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `provider_id` | [ID](./ID.md) | 是 | 目标提供方 | 类型约束见对应对象 |
| `secret` | [SecretValue](./SecretValue.md) | 是 | 待加密值 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 运行时约束

- 日志/缓存/trace禁止记录secret；前端与模型不可读取秘密。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "provider_id": "example_001",
  "secret": "EXAMPLE_ONLY_SECRET"
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.AdminSecretsPutRequest`。
