# tool.failure

状态：契约0.1，待实现。类别：细分组件私有接口。所属：工具运行。

失败恢复与等价切换的私有阶段输入。

[分类索引](../COMPONENT.md) · [统一规则](../CONVENTIONS.md) · [实际范围](../../implementation/README.md)

## 调用入口

计划Python异步签名：`async def handle(request: InternalToolFailureRequest, context: TrustedExecutionContext) -> ComponentToolFailureResult`。所属入口为 `tool.failure`。该签名是契约目标；实际方法定位见对应开发设计，不能从公网/LLM直接调用私有组件。

## 输入

[InternalToolFailureRequest](../objects/InternalToolFailureRequest.md)；每个字段的类型、必填性、默认注解、限制和分支见对象页。

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `failure` | [ToolFailure](../objects/ToolFailure.md) | 是 | 真实失败原因；不可仅凭retryable跳过未知效果核验。 |
| `equivalence_contract_ref` | [Ref](../objects/Ref.md) | 否 | 能力、信息范围与效果已登记等价的替代契约。 |
| `remaining_budget` | [Budget](../objects/Budget.md) | 是 | 父账本核准剩余额度，仅是快照，调度前仍预留。 |
| `attempts` | [Count](../objects/Count.md) | 是 | 已执行尝试总数，包括首次与失败；用于重试上限。 |

## 输出

[ComponentToolFailureResult](../objects/ComponentToolFailureResult.md) 为完整返回结构。`kind=ok` 的payload是 [RecoveryDecision](../objects/RecoveryDecision.md)。`waiting`带wait_ref，其他非成功状态带Failure，不能用空对象假装成功。

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
- 每次尝试记录实际provider、等价契约版本、用量与恢复原因。
- 按参数/权限/业务/基础设施/限流/unknown分类
- 权限拒绝不重试绕过，参数错误交Agent修复
- 只读或确认幂等瞬时错误在剩余deadline内退避
- 熔断仅阻止故障提供方新调用
- 等价契约满足才切换，否则返回能力差异让Agent决定
- unknown写先走效果对账
- 取消/超时遵从COMMON_CONTRACTS；所有引用必须当前权限内、版本可访问。

## 错误、等待、取消

- 最大尝试/时间达到返回retry_exhausted
- 非等价候选只建议
- 业务不满足不假装网络恢复可解决

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
  "attempts": 0
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
| `tool.failure` | [开发设计](../../../docs/design/components/tool-failure.md) | `src/uaw/tool/failure.py` |

[接口机器目录](../../../contracts/interfaces.json) · [统一对象schema](../../../contracts/uaw.schema.json)
