# ModelCall

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：模型调用。

统一模型调用。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `context_snapshot_ref` | [Ref](./Ref.md) | 是 | 快照 | 类型约束见对应对象 |
| `model_config` | [ResolvedModelConfig](./ResolvedModelConfig.md) | 是 | 真实配置 | 类型约束见对应对象 |
| `output_protocol` | [Protocol](./Protocol.md) | 是 | 结果协议 | 类型约束见对应对象 |
| `output_schema` | [Schema](./Schema.md) | 否 | json_schema时必需 | 类型约束见对应对象 |
| `attempt_id` | [ID](./ID.md) | 是 | 尝试 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## allOf结构规则

```json
{
  "allOf": [
    {
      "if": {
        "properties": {
          "output_protocol": {
            "const": "json_schema"
          }
        },
        "required": [
          "output_protocol"
        ]
      },
      "then": {
        "required": [
          "output_schema"
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
  "context_snapshot_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "model_config": {
    "model_id": "example_001",
    "catalog_revision": 0,
    "provider_ref": {
      "kind": "web",
      "id": "example_001",
      "version": "example_001"
    },
    "policy_ref": {
      "kind": "web",
      "id": "example_001",
      "version": "example_001"
    },
    "max_output_tokens": 0
  },
  "output_protocol": "text",
  "attempt_id": "example_001"
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.ModelCall`。
