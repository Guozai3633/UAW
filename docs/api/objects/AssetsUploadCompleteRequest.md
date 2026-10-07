# AssetsUploadCompleteRequest

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：上下文与资料。

确认上传并校验。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `upload_id` | [ID](./ID.md) | 是 | 事务 | 类型约束见对应对象 |
| `content_hash` | [Hash](./Hash.md) | 是 | 整体摘要 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 运行时约束

- 只有真实字节/摘要/格式检查通过才发布asset_ref。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "upload_id": "example_001",
  "content_hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.AssetsUploadCompleteRequest`。
