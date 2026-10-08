# RunnerReceipt

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：工作区与交付。

设备回执不能把启动成功当任务完成。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `command_id` | [ID](./ID.md) | 是 | 对应命令 | 类型约束见对应对象 |
| `attempt_id` | [ID](./ID.md) | 是 | 实际执行 | 类型约束见对应对象 |
| `kind` | [RunnerReceiptKind](./RunnerReceiptKind.md) | 是 | 成功/等待/失败 | 类型约束见对应对象 |
| `payload` | [RunnerSuccessPayload](./RunnerSuccessPayload.md) | 否 | 成功结果 | 类型约束见对应对象 |
| `wait_ref` | [Ref](./Ref.md) | 否 | 等待进程/授权 | 类型约束见对应对象 |
| `failure` | [Failure](./Failure.md) | 否 | 失败详情 | 类型约束见对应对象 |
| `usage` | [Usage](./Usage.md) | 是 | 实际消耗 | 类型约束见对应对象 |
| `signature` | [NonEmptyText](./NonEmptyText.md) | 是 | 设备签名 | 类型约束见对应对象 |

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
          "anyOf": [
            {
              "required": [
                "wait_ref"
              ]
            },
            {
              "required": [
                "failure"
              ]
            }
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
          "anyOf": [
            {
              "required": [
                "payload"
              ]
            },
            {
              "required": [
                "failure"
              ]
            }
          ]
        }
      }
    },
    {
      "if": {
        "properties": {
          "kind": {
            "enum": [
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
          "anyOf": [
            {
              "required": [
                "payload"
              ]
            },
            {
              "required": [
                "wait_ref"
              ]
            }
          ]
        }
      }
    },
    {
      "if": {
        "properties": {
          "kind": {
            "const": "cancelled"
          }
        },
        "required": [
          "kind"
        ]
      },
      "then": {
        "properties": {
          "failure": {
            "properties": {
              "category": {
                "const": "cancelled"
              }
            }
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
  "command_id": "example_001",
  "attempt_id": "example_001",
  "kind": "ok",
  "usage": {
    "attempt_id": "example_001",
    "resources": {
      "currency": "CNY",
      "input_tokens": 0,
      "output_tokens": 0,
      "model_calls": 0,
      "tool_calls": 0,
      "child_agents": 0,
      "wall_time_ms": 0,
      "money": "0"
    },
    "billing_state": "confirmed"
  },
  "signature": "example_001",
  "payload": {
    "action": "workspace.capture",
    "result": {
      "id": "example_001",
      "kind": "commit",
      "source_ref": {
        "kind": "web",
        "id": "example_001",
        "version": "example_001"
      },
      "manifest": {
        "version": "example_001",
        "input_refs": [],
        "dependency_refs": [],
        "content_hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
      },
      "include_rules": {
        "include_uncommitted": true,
        "include_untracked": true,
        "include_paths": [],
        "exclude_paths": [],
        "max_total_bytes": 0
      },
      "created_at": "2026-10-07T02:00:00Z"
    }
  }
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.RunnerReceipt`。
