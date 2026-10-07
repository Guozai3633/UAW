# DeletionReceipt

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：公共协议。

删除回执含派生失效，不掩盖异步物理清除。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `deletion_id` | [ID](./ID.md) | 是 | 删除事务 | 类型约束见对应对象 |
| `deleted_refs` | 数组&lt;[Ref](./Ref.md)&gt; | 是 | 逻辑删除 | 最少项 `0`；最多项 `256` |
| `invalidated_refs` | 数组&lt;[Ref](./Ref.md)&gt; | 是 | 索引/缓存失效 | 最少项 `0`；最多项 `256` |
| `physical_cleanup_pending` | [Bool](./Bool.md) | 是 | 物理回收状态 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "deletion_id": "example_001",
  "deleted_refs": [],
  "invalidated_refs": [],
  "physical_cleanup_pending": true
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.DeletionReceipt`。
