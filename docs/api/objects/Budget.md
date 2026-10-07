# Budget

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：运行与会话。

运行总预算/子预算请求。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `limits` | [ResourceVector](./ResourceVector.md) | 是 | 总上限 | 类型约束见对应对象 |
| `max_steps` | [Count](./Count.md) | 是 | 动作循环次数上限 | 类型约束见对应对象 |
| `max_depth` | [Count](./Count.md) | 是 | 委派最大深度 | 类型约束见对应对象 |
| `deadline` | [Timestamp](./Timestamp.md) | 是 | 绝对截止 | 类型约束见对应对象 |
| `parent_reservation_ref` | [Ref](./Ref.md) | 否 | 父预留引用 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 运行时约束

- 实际执行上限必须正值且不高于父预算/平台政策；未知费用待对账，不记零。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "limits": {
    "input_tokens": 0,
    "output_tokens": 0,
    "model_calls": 0,
    "tool_calls": 0,
    "child_agents": 0,
    "wall_time_ms": 0,
    "money": "0",
    "currency": "CNY"
  },
  "max_steps": 0,
  "max_depth": 0,
  "deadline": "2026-10-07T02:00:00Z"
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.Budget`。
