# FileContent

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：工作区与交付。

有限文本；大文件以引用和游标读取。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `workspace_ref` | [Ref](./Ref.md) | 是 | 工作区版本 | 类型约束见对应对象 |
| `path` | [RelativePath](./RelativePath.md) | 是 | 根内路径 | 类型约束见对应对象 |
| `encoding` | [NonEmptyText](./NonEmptyText.md) | 是 | 例如utf-8 | 类型约束见对应对象 |
| `text` | [Text](./Text.md) | 是 | 本页内容 | 类型约束见对应对象 |
| `content_hash` | [Hash](./Hash.md) | 是 | 整个文件摘要 | 类型约束见对应对象 |
| `location` | [Location](./Location.md) | 是 | 页/行范围 | 类型约束见对应对象 |
| `next_cursor` | [Cursor](./Cursor.md) | 否 | 下一页 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "workspace_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "path": "src/main.py",
  "encoding": "example_001",
  "text": "example_001",
  "content_hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "location": {
    "kind": "whole"
  }
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.FileContent`。
