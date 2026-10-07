# model.recovery

状态：契约0.1，待实现。类别：细分组件私有接口。所属：模型调用。

调用恢复的私有阶段输入。

[分类索引](../COMPONENT.md) · [统一规则](../CONVENTIONS.md) · [实际范围](../../implementation/README.md)

## 调用入口

计划Python异步签名：`async def handle(request: InternalModelRecoveryRequest, context: TrustedExecutionContext) -> ComponentModelRecoveryResult`。所属入口为 `model.recovery`。该签名是契约目标；实际方法定位见对应开发设计，不能从公网/LLM直接调用私有组件。

## 输入

[InternalModelRecoveryRequest](../objects/InternalModelRecoveryRequest.md)；每个字段的类型、必填性、默认注解、限制和分支见对象页。

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `failure` | [ModelFailure](../objects/ModelFailure.md) | 是 | 真实失败原因；不可仅凭retryable跳过未知效果核验。 |
| `previous_attempt_ref` | [Ref](../objects/Ref.md) | 是 | 上一次真实模型尝试，流式已有输出时避免重复呈现。 |
| `remaining_budget` | [Budget](../objects/Budget.md) | 是 | 父账本核准剩余额度，仅是快照，调度前仍预留。 |
| `retry_policy_ref` | [Ref](../objects/Ref.md) | 是 | 次数、退避、截止、等价切换限制的固定版本。 |

## 输出

[ComponentModelRecoveryResult](../objects/ComponentModelRecoveryResult.md) 为完整返回结构。`kind=ok` 的payload是 [RecoveryDecision](../objects/RecoveryDecision.md)。`waiting`带wait_ref，其他非成功状态带Failure，不能用空对象假装成功。

| payload字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `action` | [RecoveryAction](../objects/RecoveryAction.md) | 是 | 可执行恢复 |
| `retry_after_ms` | [Duration](../objects/Duration.md) | 否 | 等待 |
| `replacement_ref` | [Ref](../objects/Ref.md) | 否 | 仅已授权等价提供方/Auto模型 |
| `reason` | [NonEmptyText](../objects/NonEmptyText.md) | 是 | 依据 |

## 约束与提交

- 效果分类：`read`。
- 认证/上下文：`service`；范围及权限由服务端或Runner取得。
- 请求/动作ID去重与CAS按[统一规则](../CONVENTIONS.md)执行，重复ID不同参数必须冲突。
- 新attempt与同一逻辑生成关联；旧输出保留诊断但不能成为有效动作提案。
- 分类限流/网络/协议/参数/取消错误
- 同固定模型的瞬时失败有限退避
- Auto仅在许可兼容候选内切换
- 中途流失败新attempt从确定边界重启，不将两次delta拼接
- 记录全部失败费用并按重复无进展停止
- 取消/超时遵从COMMON_CONTRACTS；所有引用必须当前权限内、版本可访问。

## 错误、等待、取消

- 参数错误回Agent/Context修复
- 固定模型持续失败明确说明
- 取消不自动重试

错误对象是 [Failure](../objects/Failure.md)；统一分类：schema_invalid / permission_denied / feature_disabled / revision_conflict / stale_resource / dependency_unavailable / budget_exceeded / deadline_exceeded / cancelled / unknown_effect。实际Runtime需要把业务错误映射到此对象；上述分类不会代替明确failed_phase和恢复提示。

只读可在有界策略内重试；写失败先核对动作账本，效果unknown时禁止盲重试；waiting通过审批决定、用户输入、process.poll或agents.wait推进。取消只停止后续执行，已有效果如实保留。

## 请求示例

示例展示结构；不代表这些示例引用存在。

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

## 成功结构示例

```json
{
  "kind": "ok",
  "payload": {
    "action": "retry",
    "reason": "example_001"
  },
  "output_refs": []
}
```

## 拒绝结构示例

```json
{
  "kind": "denied",
  "output_refs": [],
  "failure": {
    "code": "permission_denied",
    "category": "authorization",
    "message": "当前主体没有本动作所需权限。",
    "retryable": false,
    "failed_phase": "policy_gate",
    "recover_hint": "取得真实授权后重新检查；不能通过换工具绕过。"
  }
}
```

## 模块与目录

| 节点 | 详细策略 | 计划代码位置 |
| --- | --- | --- |
| `model.recovery` | [开发设计](../../../docs/design/components/model-recovery.md) | `src/uaw/model/recovery.py` |

[接口机器目录](../../../contracts/interfaces.json) · [统一对象schema](../../../contracts/uaw.schema.json)
