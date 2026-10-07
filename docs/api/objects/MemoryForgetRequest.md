# MemoryForgetRequest

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：上下文与资料。

删除用户选中的记忆。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `conversation_id` | [ID](./ID.md) | 是 | 会话 | 类型约束见对应对象 |
| `selector` | [MemorySelector](./MemorySelector.md) | 是 | 非空限定选择 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 运行时约束

- 禁止空选择器全量删除；失效索引、摘要和缓存；后续调用不能读旧记忆派生块。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "conversation_id": "example_001",
  "selector": {
    "ids": [
      "example_001"
    ]
  }
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.MemoryForgetRequest`。
