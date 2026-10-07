# ToolArtifactsPublishInput

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：工作区与交付。

登记成果以便预览、下载、修订。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `content_ref` | [Ref](./Ref.md) | 是 | 真实内容 | 类型约束见对应对象 |
| `title` | [NonEmptyText](./NonEmptyText.md) | 是 | 标题 | 类型约束见对应对象 |
| `format_kind` | [NonEmptyText](./NonEmptyText.md) | 是 | 格式 | 类型约束见对应对象 |
| `provenance_refs` | 数组&lt;[Ref](./Ref.md)&gt; | 是 | 来源 | 最少项 `0`；最多项 `256` |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 运行时约束

- 仅登记，不是部署或公开发布；内容须真实存在且可访问。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "content_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "title": "example_001",
  "format_kind": "example_001",
  "provenance_refs": []
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.ToolArtifactsPublishInput`。
