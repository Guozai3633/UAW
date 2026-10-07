# ModelRequest

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：模型调用。

用户模型意图，尚未解析为实际模型配置。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `mode` | [ModelMode](./ModelMode.md) | 是 | inherit/explicit/auto | 类型约束见对应对象 |
| `requested_name` | [NonEmptyText](./NonEmptyText.md) | 否 | explicit时用户原指定名 | 类型约束见对应对象 |
| `source_input_ref` | [UserInputRef](./UserInputRef.md) | 否 | 明确覆盖/Auto授权来源 | 类型约束见对应对象 |
| `allowed_model_ids` | 数组&lt;[ID](./ID.md)&gt; | 否 | Auto授权范围 | 最少项 `0`；最多项 `64` |

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
          "requested_name",
          "source_input_ref"
        ]
      }
    },
    {
      "if": {
        "properties": {
          "mode": {
            "const": "inherit"
          }
        },
        "required": [
          "mode"
        ]
      },
      "then": {
        "not": {
          "required": [
            "requested_name"
          ]
        }
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
        "required": [
          "source_input_ref"
        ]
      }
    }
  ]
}
```

## 运行时约束

- inherit不得填requested_name；explicit必需requested_name和用户来源；auto须有效授权且无静默扩范围。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "mode": "inherit"
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.ModelRequest`。
