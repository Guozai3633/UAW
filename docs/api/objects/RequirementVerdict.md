# RequirementVerdict

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：Agent执行与协作。

语义核验逐条覆盖要求。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `requirement_id` | [ID](./ID.md) | 是 | 要求 | 类型约束见对应对象 |
| `state` | [CheckState](./CheckState.md) | 是 | 判定 | 类型约束见对应对象 |
| `evidence_refs` | 数组&lt;[Ref](./Ref.md)&gt; | 是 | 实际证据 | 最少项 `0`；最多项 `256` |
| `reason` | [NonEmptyText](./NonEmptyText.md) | 是 | 判定依据 | 类型约束见对应对象 |
| `limitations` | 数组&lt;[NonEmptyText](./NonEmptyText.md)&gt; | 是 | 缺口 | 最少项 `0`；最多项 `256` |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## allOf结构规则

```json
{
  "allOf": [
    {
      "if": {
        "properties": {
          "state": {
            "const": "passed"
          }
        },
        "required": [
          "state"
        ]
      },
      "then": {
        "properties": {
          "evidence_refs": {
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
  "requirement_id": "example_001",
  "state": "passed",
  "evidence_refs": [
    {
      "kind": "web",
      "id": "example_001",
      "version": "example_001"
    }
  ],
  "reason": "example_001",
  "limitations": []
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.RequirementVerdict`。
