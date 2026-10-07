# ToolResult

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：工具运行。

基础设施响应成功和业务成功分别表达。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `call_ref` | [Ref](./Ref.md) | 是 | 真实调用 | 类型约束见对应对象 |
| `status` | [ToolStatus](./ToolStatus.md) | 是 | 成功/失败/等待/未知效果 | 类型约束见对应对象 |
| `data` | [Object](./Object.md) | 否 | 由该工具output_schema约束的业务数据 | 类型约束见对应对象 |
| `output_refs` | 数组&lt;[Ref](./Ref.md)&gt; | 是 | 大结果/文件/证据 | 最少项 `0`；最多项 `256` |
| `failure` | [Failure](./Failure.md) | 否 | 失败 | 类型约束见对应对象 |
| `effect_state` | [EffectState](./EffectState.md) | 是 | 副作用确定性 | 类型约束见对应对象 |
| `usage_ref` | [Ref](./Ref.md) | 是 | 调用用量 | 类型约束见对应对象 |
| `next_cursor` | [Cursor](./Cursor.md) | 否 | 分页 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## allOf结构规则

```json
{
  "allOf": [
    {
      "if": {
        "properties": {
          "status": {
            "const": "failed"
          }
        },
        "required": [
          "status"
        ]
      },
      "then": {
        "required": [
          "failure"
        ]
      }
    },
    {
      "if": {
        "properties": {
          "status": {
            "const": "succeeded"
          }
        },
        "required": [
          "status"
        ]
      },
      "then": {
        "properties": {
          "effect_state": {
            "const": "confirmed"
          }
        }
      }
    }
  ]
}
```

## 运行时约束

- failed须failure；unknown效果不得自动重放非幂等写；succeeded须实际回执或可验证只读结果。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "call_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "status": "succeeded",
  "output_refs": [],
  "effect_state": "confirmed",
  "usage_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  }
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.ToolResult`。
