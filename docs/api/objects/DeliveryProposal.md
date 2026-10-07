# DeliveryProposal

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：Agent执行与协作。

候选完成提案，不能由模型直接置Run为completed。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `run_ref` | [Ref](./Ref.md) | 是 | 目标运行版本 | 类型约束见对应对象 |
| `contract_ref` | [Ref](./Ref.md) | 是 | 交付标准 | 类型约束见对应对象 |
| `outcome` | [Outcome](./Outcome.md) | 是 | 建议终态 | 类型约束见对应对象 |
| `artifact_refs` | 数组&lt;[Ref](./Ref.md)&gt; | 是 | 成果版本 | 最少项 `0`；最多项 `256` |
| `report_ref` | [Ref](./Ref.md) | 是 | 语义及执行证据报告 | 类型约束见对应对象 |
| `unresolved_effect_refs` | 数组&lt;[Ref](./Ref.md)&gt; | 是 | 未确认外部效果 | 最少项 `0`；最多项 `256` |
| `created_at` | [Timestamp](./Timestamp.md) | 是 | 提案时间 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## allOf结构规则

```json
{
  "allOf": [
    {
      "if": {
        "properties": {
          "outcome": {
            "const": "succeeded"
          }
        },
        "required": [
          "outcome"
        ]
      },
      "then": {
        "properties": {
          "unresolved_effect_refs": {
            "maxItems": 0
          }
        }
      }
    }
  ]
}
```

## 运行时约束

- 必需要求缺证据、成果过期或未知写效果时不得标记全部成功。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "run_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "contract_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "outcome": "succeeded",
  "artifact_refs": [],
  "report_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "unresolved_effect_refs": [],
  "created_at": "2026-10-07T02:00:00Z"
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.DeliveryProposal`。
