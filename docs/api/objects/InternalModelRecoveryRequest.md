# InternalModelRecoveryRequest

状态：对象契约0.1；可用范围见具体接口与实施记录。所属：模型调用。

调用恢复的私有阶段输入。

[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)

## 字段

| 字段 | 类型 | 必填 | 含义 | 结构约束 |
| --- | --- | --- | --- | --- |
| `failure` | [ModelFailure](./ModelFailure.md) | 是 | 真实失败原因；不可仅凭retryable跳过未知效果核验。 | 类型约束见对应对象 |
| `previous_attempt_ref` | [Ref](./Ref.md) | 是 | 上一次真实模型尝试，流式已有输出时避免重复呈现。 | 类型约束见对应对象 |
| `remaining_budget` | [Budget](./Budget.md) | 是 | 父账本核准剩余额度，仅是快照，调度前仍预留。 | 类型约束见对应对象 |
| `retry_policy_ref` | [Ref](./Ref.md) | 是 | 次数、退避、截止、等价切换限制的固定版本。 | 类型约束见对应对象 |

拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。

## 运行时约束

- 新attempt与同一逻辑生成关联；旧输出保留诊断但不能成为有效动作提案。
- 服务端注入可信上下文，不通过HTTP或LLM工具直接访问。

## 结构示例

以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。

```json
{
  "failure": {
    "code": "example_001",
    "category": "arguments",
    "message": "example_001",
    "retryable": true,
    "failed_phase": "example_001"
  },
  "previous_attempt_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "remaining_budget": {
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
  },
  "retry_policy_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  }
}
```

## 机器契约

[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs.InternalModelRecoveryRequest`。
