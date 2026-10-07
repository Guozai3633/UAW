# UploadSession

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：上下文与资料。

二进制上传不塞入模型或普通JSON。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `id` | [ID](./ID.md) | 是 | 上传ID | 类型约束见对应对象 |
| `put_url` | [URL](./URL.md) | 是 | 一次性上传地址 | 类型约束见对应对象 |
| `expires_at` | [Timestamp](./Timestamp.md) | 是 | 截止 | 类型约束见对应对象 |
| `max_bytes` | [UploadSize](./UploadSize.md) | 是 | 限制 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "id": "example_001",
  "put_url": "https://example.org/resource",
  "expires_at": "2026-10-07T02:00:00Z",
  "max_bytes": 1
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.UploadSession`。
