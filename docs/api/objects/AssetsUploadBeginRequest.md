# AssetsUploadBeginRequest

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：上下文与资料。

申请上传事务。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `file_name` | [NonEmptyText](./NonEmptyText.md) | 是 | 展示文件名 | 类型约束见对应对象 |
| `media_type` | [NonEmptyText](./NonEmptyText.md) | 是 | 声称格式 | 类型约束见对应对象 |
| `size_bytes` | [UploadSize](./UploadSize.md) | 是 | 总大小 | 类型约束见对应对象 |
| `content_hash` | [Hash](./Hash.md) | 是 | 整体摘要 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "file_name": "example_001",
  "media_type": "example_001",
  "size_bytes": 1,
  "content_hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.AssetsUploadBeginRequest`。
