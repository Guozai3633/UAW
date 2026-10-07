# HttpMemoryForgetResult

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：上下文与资料。

该接口的状态结果；ok才携带完整业务payload。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `kind` | enum: `ok` / `waiting` / `missing` / `denied` / `conflict` / `stale` / `failed` / `cancelled` | 是 | 接口状态 | — |
| `payload` | [DeletionReceipt](./DeletionReceipt.md) | 否 | ok的业务结果 | 类型约束见对应对象 |
| `output_refs` | 数组&lt;[Ref](./Ref.md)&gt; | 是 | 关联真实资源 | 最少项 `0`；最多项 `256` |
| `revision` | [Revision](./Revision.md) | 否 | 本次提交/读取的域版本 | 类型约束见对应对象 |
| `failure` | [Failure](./Failure.md) | 否 | 失败状态的明确原因 | 类型约束见对应对象 |
| `wait_ref` | [Ref](./Ref.md) | 否 | waiting时审批/进程/用户问题引用 | 类型约束见对应对象 |
| `usage_ref` | [Ref](./Ref.md) | 否 | 发生消耗时真实统计 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## allOf结构规则

```json
{
  "allOf": [
    {
      "if": {
        "properties": {
          "kind": {
            "const": "ok"
          }
        },
        "required": [
          "kind"
        ]
      },
      "then": {
        "required": [
          "payload"
        ],
        "not": {
          "required": [
            "failure"
          ]
        }
      }
    },
    {
      "if": {
        "properties": {
          "kind": {
            "const": "waiting"
          }
        },
        "required": [
          "kind"
        ]
      },
      "then": {
        "required": [
          "wait_ref"
        ],
        "not": {
          "required": [
            "payload"
          ]
        }
      }
    },
    {
      "if": {
        "properties": {
          "kind": {
            "enum": [
              "missing",
              "denied",
              "conflict",
              "stale",
              "failed",
              "cancelled"
            ]
          }
        },
        "required": [
          "kind"
        ]
      },
      "then": {
        "required": [
          "failure"
        ],
        "not": {
          "required": [
            "payload"
          ]
        }
      }
    }
  ]
}
```

## 运行时约束

- ok必需payload且不含failure；waiting必需wait_ref；其他状态必需failure；取消不回滚已确认外部动作。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "kind": "ok",
  "output_refs": [],
  "payload": {
    "deletion_id": "example_001",
    "deleted_refs": [],
    "invalidated_refs": [],
    "physical_cleanup_pending": true
  }
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.HttpMemoryForgetResult`。
