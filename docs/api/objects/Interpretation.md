# Interpretation

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：任务理解。

一个有来源的理解候选。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `goal` | [NonEmptyText](./NonEmptyText.md) | 是 | 候选目标 | 类型约束见对应对象 |
| `assumptions` | 数组&lt;[NonEmptyText](./NonEmptyText.md)&gt; | 是 | 未获用户确认的假设 | 最少项 `0`；最多项 `256` |
| `source_refs` | 数组&lt;[Ref](./Ref.md)&gt; | 是 | 原文与补充来源 | 最少项 `0`；最多项 `256` |
| `missing_facts` | 数组&lt;[NonEmptyText](./NonEmptyText.md)&gt; | 是 | 缺少的信息 | 最少项 `0`；最多项 `256` |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "goal": "example_001",
  "assumptions": [],
  "source_refs": [],
  "missing_facts": []
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.Interpretation`。
