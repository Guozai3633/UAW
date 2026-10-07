# ReviewSet

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：工作区与交付。

用户审阅交付或修改集。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `id` | [ID](./ID.md) | 是 | 审阅 | 类型约束见对应对象 |
| `revision` | [Revision](./Revision.md) | 是 | 版本 | 类型约束见对应对象 |
| `target_refs` | 数组&lt;[Ref](./Ref.md)&gt; | 是 | 固定成果/变更版本 | 最少项 `0`；最多项 `256` |
| `unit_ids` | 数组&lt;[ID](./ID.md)&gt; | 是 | 可选择单位 | 最少项 `0`；最多项 `256` |
| `decision` | [DeliveryDecision](./DeliveryDecision.md) | 否 | 最新用户意见 | 类型约束见对应对象 |
| `feedback_refs` | 数组&lt;[Ref](./Ref.md)&gt; | 是 | 位置反馈 | 最少项 `0`；最多项 `256` |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "id": "example_001",
  "revision": 0,
  "target_refs": [],
  "unit_ids": [],
  "feedback_refs": []
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.ReviewSet`。
