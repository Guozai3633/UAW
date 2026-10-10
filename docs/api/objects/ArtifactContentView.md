# ArtifactContentView

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：工作区与交付。

实际文本或Markdown成果正文。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `artifact` | [ArtifactRecord](./ArtifactRecord.md) | 是 | 不可变成果元数据 | 类型约束见对应对象 |
| `content` | [ArtifactPreviewText](./ArtifactPreviewText.md) | 是 | 完整正文 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "artifact": {
    "id": "example_001",
    "version": "example_001",
    "title": "example_001",
    "format_kind": "example_001",
    "media_type": "example_001",
    "content_ref": {
      "kind": "web",
      "id": "example_001",
      "version": "example_001"
    },
    "size_bytes": 0,
    "content_hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
    "provenance_refs": [],
    "verification_refs": [],
    "created_at": "2026-10-07T02:00:00Z"
  },
  "content": "example_001"
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.ArtifactContentView`。
