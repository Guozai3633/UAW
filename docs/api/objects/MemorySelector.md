# MemorySelector

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：上下文与资料。

删除/召回筛选，不接受任意数据库条件。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `ids` | 数组&lt;[ID](./ID.md)&gt; | 否 | 指定记忆 | 最少项 `1`；最多项 `256` |
| `scope` | [ScopeSelector](./ScopeSelector.md) | 否 | 限定范围 | 类型约束见对应对象 |
| `kind` | [MemoryKind](./MemoryKind.md) | 否 | 类别 | 类型约束见对应对象 |
| `slot_key` | [NonEmptyText](./NonEmptyText.md) | 否 | 冲突槽 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 运行时约束

- 删除空选择器必须拒绝；整范围删除须明确all_in_scope操作。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "ids": [
    "example_001"
  ]
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.MemorySelector`。
