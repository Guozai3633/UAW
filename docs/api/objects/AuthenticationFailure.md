# AuthenticationFailure

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：公共协议。

认证失败不透露受保护资源存在性。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `code` | [ID](./ID.md) | 是 | 稳定认证错误码 | 类型约束见对应对象 |
| `message` | [Text](./Text.md) | 是 | 安全提示 | 类型约束见对应对象 |
| `request_id` | [ID](./ID.md) | 是 | 关联 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "code": "authentication_required",
  "message": "example_001",
  "request_id": "example_001"
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.AuthenticationFailure`。
