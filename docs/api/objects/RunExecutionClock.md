# RunExecutionClock

状态：对象契约0.2 / conversation-v1；可用范围见具体接口与实施记录。所属：运行与会话。

新Run有版本主动执行时钟；旧调用/授权独立到期。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `protocol` | 常量 `conversation-v1` | 是 | 协议 | — |
| `run_id` | [ID](./ID.md) | 是 | 原Run | 类型约束见对应对象 |
| `revision` | [Revision](./Revision.md) | 是 | 持久CAS修订 | ≥ `1`；类型约束见对应对象 |
| `mode` | enum: `active` / `waiting_for_user` / `stopped` | 是 | 执行段状态 | — |
| `active_limit_ms` | [Duration](./Duration.md) | 是 | 最大主动执行时间 | ≥ `1`；类型约束见对应对象 |
| `active_elapsed_ms` | integer | 是 | 已经结束的主动段实际耗时，允许真实超额但不能再执行 | ≥ `0`；≤ `9007199254740991` |
| `wait_elapsed_ms` | integer | 是 | 已经结束的等待耗时，与主动时间上限分别计量 | ≥ `0`；≤ `9007199254740991` |
| `captured_at` | [Timestamp](./Timestamp.md) | 是 | 可信服务采集时间 | 类型约束见对应对象 |
| `active_since` | [Timestamp](./Timestamp.md) | 否 | active时必需，最近主动段起点 | 类型约束见对应对象 |
| `waiting_since` | [Timestamp](./Timestamp.md) | 否 | 等待时必需，当前等待起点 | 类型约束见对应对象 |
| `waiting_item_ref` | [ConversationItemRef](./ConversationItemRef.md) | 否 | 等待问题或人工审批的稳定Item | 类型约束见对应对象 |
| `in_flight_refs` | 数组&lt;[Ref](./Ref.md)&gt; | 是 | 原已派发且未结束调用；不能当免费暂停 | 最少项 `0`；最多项 `64` |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## allOf结构规则

```json
{
  "allOf": [
    {
      "if": {
        "properties": {
          "mode": {
            "const": "active"
          }
        },
        "required": [
          "mode"
        ]
      },
      "then": {
        "required": [
          "active_since"
        ],
        "not": {
          "anyOf": [
            {
              "required": [
                "waiting_since"
              ]
            },
            {
              "required": [
                "waiting_item_ref"
              ]
            }
          ]
        }
      }
    },
    {
      "if": {
        "properties": {
          "mode": {
            "const": "waiting_for_user"
          }
        },
        "required": [
          "mode"
        ]
      },
      "then": {
        "required": [
          "waiting_since",
          "waiting_item_ref"
        ],
        "not": {
          "required": [
            "active_since"
          ]
        },
        "properties": {
          "in_flight_refs": {
            "maxItems": 0
          }
        }
      }
    },
    {
      "if": {
        "properties": {
          "mode": {
            "const": "stopped"
          }
        },
        "required": [
          "mode"
        ]
      },
      "then": {
        "not": {
          "anyOf": [
            {
              "required": [
                "active_since"
              ]
            },
            {
              "required": [
                "waiting_since"
              ]
            },
            {
              "required": [
                "waiting_item_ref"
              ]
            }
          ]
        }
      }
    }
  ]
}
```

## 运行时约束

- 时间只由可信Run服务采集；active_since/waiting_since不能晚于captured_at；真实耗时超额照实保存，剩余归0且不能续领时间。
- 主动段并集计时；未知在途调用不得转waiting免费暂停；进程重启/租约丢失按持久段对账，不重领完整预算。
- 预算deadline原0.1语义不改；新Run按协议绑定使用此时钟派生尚未发送调用的期限，已经发送的ctx/deadline不修改。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "protocol": "conversation-v1",
  "run_id": "example_001",
  "revision": 1,
  "mode": "active",
  "active_limit_ms": 1,
  "active_elapsed_ms": 0,
  "wait_elapsed_ms": 0,
  "captured_at": "2026-10-07T02:00:00Z",
  "in_flight_refs": [],
  "active_since": "2026-10-07T02:00:00Z"
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.RunExecutionClock`。
