# DownloadTicket

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：公共协议。

授权下载句柄，不能视为公开URL。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `url` | [URL](./URL.md) | 是 | 短期地址 | 类型约束见对应对象 |
| `expires_at` | [Timestamp](./Timestamp.md) | 是 | 有效期 | 类型约束见对应对象 |
| `resource_ref` | [Ref](./Ref.md) | 是 | 目标 | 类型约束见对应对象 |
| `content_hash` | [Hash](./Hash.md) | 是 | 摘要 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "url": "https://example.org/resource",
  "expires_at": "2026-10-07T02:00:00Z",
  "resource_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "content_hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.DownloadTicket`。
