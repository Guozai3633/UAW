# ItemPatch

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：运行与会话。

增量文本不可与整段替换混淆。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `item_id` | [ID](./ID.md) | 是 | 项 | 类型约束见对应对象 |
| `base_revision` | [Revision](./Revision.md) | 是 | 原版本 | 类型约束见对应对象 |
| `status` | [ItemStatus](./ItemStatus.md) | 否 | 新状态 | 类型约束见对应对象 |
| `text_delta` | [Text](./Text.md) | 否 | 追加文本 | 类型约束见对应对象 |
| `replacement_text` | [Text](./Text.md) | 否 | 完整替换 | 类型约束见对应对象 |
| `resource_refs` | 数组&lt;[Ref](./Ref.md)&gt; | 否 | 替换资源 | 最少项 `0`；最多项 `256` |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## anyOf结构规则

```json
{
  "anyOf": [
    {
      "required": [
        "status"
      ]
    },
    {
      "required": [
        "text_delta"
      ]
    },
    {
      "required": [
        "replacement_text"
      ]
    },
    {
      "required": [
        "resource_refs"
      ]
    }
  ]
}
```

## not结构规则

```json
{
  "not": {
    "required": [
      "text_delta",
      "replacement_text"
    ]
  }
}
```

## 运行时约束

- text_delta与replacement_text不能同时存在；至少一个变更字段；项终态不能继续delta。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "item_id": "example_001",
  "base_revision": 0,
  "status": "pending"
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.ItemPatch`。
