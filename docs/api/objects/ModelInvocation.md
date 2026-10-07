# ModelInvocation

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：模型调用。

持久调用意图；claimed重读不能再发送，finished只重放保存的回执。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `id` | [ID](./ID.md) | 是 | 逻辑调用 | 类型约束见对应对象 |
| `run_id` | [ID](./ID.md) | 是 | 运行 | 类型约束见对应对象 |
| `request_hash` | [Hash](./Hash.md) | 是 | 精确请求及可信关联摘要 | 类型约束见对应对象 |
| `request` | [ModelCall](./ModelCall.md) | 是 | 固定输入引用、配置与协议 | 类型约束见对应对象 |
| `operation_id` | [ID](./ID.md) | 是 | 操作 | 类型约束见对应对象 |
| `trace_id` | [ID](./ID.md) | 是 | 链路 | 类型约束见对应对象 |
| `state` | [NonEmptyText](./NonEmptyText.md) | 是 | claimed或finished | 类型约束见对应对象 |
| `result` | [Object](./Object.md) | 否 | 已校验的Runtime结果 | 类型约束见对应对象 |
| `created_at` | [Timestamp](./Timestamp.md) | 是 | 受理时间 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## allOf结构规则

```json
{
  "allOf": [
    {
      "if": {
        "properties": {
          "state": {
            "const": "finished"
          }
        },
        "required": [
          "state"
        ]
      },
      "then": {
        "required": [
          "result"
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
  "run_id": "example_001",
  "request_hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "request": {
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
  },
  "operation_id": "example_001",
  "trace_id": "example_001",
  "state": "claimed",
  "created_at": "2026-10-07T02:00:00Z"
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.ModelInvocation`。
