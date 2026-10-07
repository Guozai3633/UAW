# ArtifactRecord

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：工作区与交付。

用户可编辑、预览、导出的版本化成果。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `id` | [ID](./ID.md) | 是 | 成果 | 类型约束见对应对象 |
| `version` | [Version](./Version.md) | 是 | 内容版本 | 类型约束见对应对象 |
| `title` | [NonEmptyText](./NonEmptyText.md) | 是 | 展示名 | 类型约束见对应对象 |
| `format_kind` | [NonEmptyText](./NonEmptyText.md) | 是 | 例如markdown/csv/source_code | 类型约束见对应对象 |
| `media_type` | [NonEmptyText](./NonEmptyText.md) | 是 | MIME | 类型约束见对应对象 |
| `content_ref` | [Ref](./Ref.md) | 是 | 实际内容 | 类型约束见对应对象 |
| `size_bytes` | [Count](./Count.md) | 是 | 字节数 | 类型约束见对应对象 |
| `content_hash` | [Hash](./Hash.md) | 是 | 摘要 | 类型约束见对应对象 |
| `provenance_refs` | 数组&lt;[Ref](./Ref.md)&gt; | 是 | 生成/数据来源 | 最少项 `0`；最多项 `256` |
| `verification_refs` | 数组&lt;[Ref](./Ref.md)&gt; | 是 | 该版本证据 | 最少项 `0`；最多项 `256` |
| `created_at` | [Timestamp](./Timestamp.md) | 是 | 登记时间 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 运行时约束

- publish工具仅登记成果，不意味着公网发布；下载URL授权且短时有效。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
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
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.ArtifactRecord`。
