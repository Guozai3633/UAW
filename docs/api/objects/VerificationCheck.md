# VerificationCheck

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：Agent执行与协作。

实际执行/资料核验的证据，不能伪造运行。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `id` | [ID](./ID.md) | 是 | 检查 | 类型约束见对应对象 |
| `kind` | [VerificationKind](./VerificationKind.md) | 是 | 命令/结构/引用/语义 | 类型约束见对应对象 |
| `requirement_ids` | 数组&lt;[ID](./ID.md)&gt; | 是 | 覆盖要求 | 最少项 `0`；最多项 `256` |
| `state` | [CheckState](./CheckState.md) | 是 | passed/failed/not_run/blocked | 类型约束见对应对象 |
| `target_refs` | 数组&lt;[Ref](./Ref.md)&gt; | 是 | 核验版本 | 最少项 `0`；最多项 `256` |
| `process_ref` | [Ref](./Ref.md) | 否 | 命令检查必需 | 类型约束见对应对象 |
| `evidence_refs` | 数组&lt;[Ref](./Ref.md)&gt; | 是 | 真实证据 | 最少项 `0`；最多项 `256` |
| `summary` | [Text](./Text.md) | 是 | 解释及限制 | 类型约束见对应对象 |

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
    },
    {
      "if": {
        "properties": {
          "kind": {
            "const": "command"
          },
          "state": {
            "enum": [
              "passed",
              "failed"
            ]
          }
        },
        "required": [
          "kind",
          "state"
        ]
      },
      "then": {
        "required": [
          "process_ref"
        ]
      }
    }
  ]
}
```

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "id": "example_001",
  "kind": "command",
  "requirement_ids": [],
  "state": "passed",
  "target_refs": [],
  "evidence_refs": [
    {
      "kind": "web",
      "id": "example_001",
      "version": "example_001"
    }
  ],
  "summary": "example_001",
  "process_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  }
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.VerificationCheck`。
