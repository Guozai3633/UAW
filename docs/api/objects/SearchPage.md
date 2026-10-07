# SearchPage

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：工具运行。

稳定筛选条件的分页结果。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `items` | 数组&lt;[SearchHit](./SearchHit.md)&gt; | 是 | 本页 | 最少项 `0`；最多项 `256` |
| `next_cursor` | [Cursor](./Cursor.md) | 否 | 续页 | 类型约束见对应对象 |
| `snapshot_revision` | [Revision](./Revision.md) | 是 | 读取版本 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "items": [],
  "snapshot_revision": 0
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.SearchPage`。
