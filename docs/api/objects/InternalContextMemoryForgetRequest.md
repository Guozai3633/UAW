# InternalContextMemoryForgetRequest

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：上下文与资料。

遗忘与删除传播的私有阶段输入。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `selector` | [MemorySelector](./MemorySelector.md) | 是 | 明确范围的记忆选择，不是任意数据库查询。 | 类型约束见对应对象 |
| `deletion_id` | [ID](./ID.md) | 是 | 稳定删除事务ID，重复请求不重复删除。 | 类型约束见对应对象 |
| `derived_dependency_refs` | 数组&lt;[Ref](./Ref.md)&gt; | 是 | 待删除资源派生的索引/摘要/缓存，须传播失效。 | 最多项 `256` |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 运行时约束

- 删除记录不能被旧checkpoint/备份恢复覆盖。
- 服务端注入可信上下文，不通过HTTP或LLM工具直接访问。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "selector": {
    "ids": [
      "example_001"
    ]
  },
  "deletion_id": "example_001",
  "derived_dependency_refs": []
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.InternalContextMemoryForgetRequest`。
