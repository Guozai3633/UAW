# ResolvedModelPolicy

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：模型调用。

继承链与用户来源可核验。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `id` | [ID](./ID.md) | 是 | 模型政策 | 类型约束见对应对象 |
| `revision` | [Revision](./Revision.md) | 是 | 政策版本 | 类型约束见对应对象 |
| `mode` | enum: `explicit` / `auto` | 是 | 继承已经解析为父政策模式。 | — |
| `fixed_model_id` | [ID](./ID.md) | 否 | 固定模型 | 类型约束见对应对象 |
| `allowed_model_ids` | 数组&lt;[ID](./ID.md)&gt; | 是 | Auto候选集 | 最少项 `0`；最多项 `256` |
| `source_input_ref` | [UserInputRef](./UserInputRef.md) | 是 | 明确用户选择 | 类型约束见对应对象 |
| `parent_policy_ref` | [Ref](./Ref.md) | 否 | 继承链 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## allOf结构规则

```json
{
  "allOf": [
    {
      "if": {
        "properties": {
          "mode": {
            "const": "explicit"
          }
        },
        "required": [
          "mode"
        ]
      },
      "then": {
        "required": [
          "fixed_model_id"
        ]
      }
    },
    {
      "if": {
        "properties": {
          "mode": {
            "const": "auto"
          }
        },
        "required": [
          "mode"
        ]
      },
      "then": {
        "properties": {
          "allowed_model_ids": {
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
  "id": "example_001",
  "revision": 0,
  "mode": "explicit",
  "allowed_model_ids": [],
  "source_input_ref": {
    "kind": "input",
    "id": "example_001",
    "version": "example_001"
  },
  "fixed_model_id": "example_001"
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.ResolvedModelPolicy`。
