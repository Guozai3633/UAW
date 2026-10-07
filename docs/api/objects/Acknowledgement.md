# Acknowledgement

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：公共协议。

确认受理，不证明整个任务已完成。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `operation_id` | [ID](./ID.md) | 是 | 受理ID | 类型约束见对应对象 |
| `status` | enum: `accepted` / `unchanged` / `completed` / `pending` | 是 | 确认状态 | — |
| `related_refs` | 数组&lt;[Ref](./Ref.md)&gt; | 否 | 相关资源 | 最少项 `0`；最多项 `256` |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "operation_id": "example_001",
  "status": "accepted"
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.Acknowledgement`。
