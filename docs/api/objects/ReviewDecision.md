# ReviewDecision

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：工作区与交付。

用户意见独立于自动核验。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `decision` | [DeliveryDecision](./DeliveryDecision.md) | 是 | 接受/拒绝/修改/部分接受 | 类型约束见对应对象 |
| `selected_unit_ids` | 数组&lt;[ID](./ID.md)&gt; | 是 | partial_accept必需指定非空 | 最少项 `0`；最多项 `256` |
| `feedback` | [Text](./Text.md) | 是 | 用户理由或修订 | 类型约束见对应对象 |
| `position` | [Location](./Location.md) | 否 | 具体位置 | 类型约束见对应对象 |
| `expected_target_refs` | 数组&lt;[Ref](./Ref.md)&gt; | 是 | 基线内容 | 最少项 `0`；最多项 `256` |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## allOf结构规则

```json
{
  "allOf": [
    {
      "if": {
        "properties": {
          "decision": {
            "const": "partial_accept"
          }
        },
        "required": [
          "decision"
        ]
      },
      "then": {
        "properties": {
          "selected_unit_ids": {
            "minItems": 1
          }
        }
      }
    }
  ]
}
```

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "decision": "accept",
  "selected_unit_ids": [],
  "feedback": "example_001",
  "expected_target_refs": []
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.ReviewDecision`。
