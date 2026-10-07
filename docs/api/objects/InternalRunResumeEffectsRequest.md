# InternalRunResumeEffectsRequest

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：运行与会话。

Tool未决动作对账的私有阶段输入。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `tool_ledger_cursor` | [Cursor](./Cursor.md) | 是 | 检查点处的效果账本位置，用于续接对账。 | 类型约束见对应对象 |
| `pending_action_refs` | 数组&lt;[Ref](./Ref.md)&gt; | 是 | 未确认效果动作，恢复前需查回执。 | 最多项 `256` |
| `deadline` | [Timestamp](./Timestamp.md) | 是 | 绝对UTC截止；重试和子调用不能延长父deadline。 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 运行时约束

- Run记录对账进度引用，效果权威仍归Tool。
- 服务端注入可信上下文，不通过HTTP或LLM工具直接访问。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "tool_ledger_cursor": "example_001",
  "pending_action_refs": [],
  "deadline": "2026-10-07T02:00:00Z"
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.InternalRunResumeEffectsRequest`。
