# IntentPreviewRequest

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：任务理解。

草稿理解提示。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `conversation_id` | [ID](./ID.md) | 是 | 会话 | 类型约束见对应对象 |
| `draft_revision` | [Revision](./Revision.md) | 是 | 草稿版本 | 类型约束见对应对象 |
| `text` | [Text](./Text.md) | 是 | 原文 | 类型约束见对应对象 |
| `attachment_refs` | 数组&lt;[Ref](./Ref.md)&gt; | 是 | 材料 | 最少项 `0`；最多项 `256` |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 运行时约束

- 只读、短deadline；取消旧草稿；预览失败不阻止提交；不得创建Run或执行写。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "conversation_id": "example_001",
  "draft_revision": 0,
  "text": "example_001",
  "attachment_refs": []
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.IntentPreviewRequest`。
