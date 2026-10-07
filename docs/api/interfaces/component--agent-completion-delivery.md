# agent.completion.delivery

状态：契约0.1，待实现。类别：细分组件私有接口。所属：Agent执行与协作。

提交交付的私有阶段输入。

[分类索引](../COMPONENT.md) · [统一规则](../CONVENTIONS.md) · [实际范围](../../implementation/README.md)

## 调用入口

计划Python异步签名：`async def handle(request: InternalAgentCompletionDeliveryRequest, context: TrustedExecutionContext) -> ComponentAgentCompletionDeliveryResult`。所属入口为 `agent.completion.delivery`。该签名是契约目标；实际方法定位见对应开发设计，不能从公网/LLM直接调用私有组件。

## 输入

[InternalAgentCompletionDeliveryRequest](../objects/InternalAgentCompletionDeliveryRequest.md)；每个字段的类型、必填性、默认注解、限制和分支见对象页。

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `proposal_ref` | [Ref](../objects/Ref.md) | 是 | 已经核对版本/证据的完成提案。 |
| `expected_run_revision` | [Revision](../objects/Revision.md) | 是 | Run状态CAS修订，过期执行者不能推进新状态。 |
| `artifact_manifest_ref` | [Ref](../objects/Ref.md) | 是 | 本次交付成果的不可变清单。 |
| `proposed_outcome` | [Outcome](../objects/Outcome.md) | 是 | 建议结果；代码完成闸门验证后才提交终态。 |

## 输出

[ComponentAgentCompletionDeliveryResult](../objects/ComponentAgentCompletionDeliveryResult.md) 为完整返回结构。`kind=ok` 的payload是 [RunRecord](../objects/RunRecord.md)。`waiting`带wait_ref，其他非成功状态带Failure，不能用空对象假装成功。

| payload字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `id` | [ID](../objects/ID.md) | 是 | Run |
| `task_id` | [ID](../objects/ID.md) | 是 | 任务 |
| `conversation_id` | [ID](../objects/ID.md) | 是 | 入口会话 |
| `revision` | [Revision](../objects/Revision.md) | 是 | 状态版本 |
| `status` | [RunStatus](../objects/RunStatus.md) | 是 | 当前状态 |
| `root_agent_ref` | [Ref](../objects/Ref.md) | 否 | 根实例 |
| `frame_ref` | [Ref](../objects/Ref.md) | 否 | 当前任务理解 |
| `plan_ref` | [Ref](../objects/Ref.md) | 否 | 可选图 |
| `budget` | [Budget](../objects/Budget.md) | 是 | 上限 |
| `outcome` | [Outcome](../objects/Outcome.md) | 否 | 终态 |
| `created_at` | [Timestamp](../objects/Timestamp.md) | 是 | 受理时间 |
| `ended_at` | [Timestamp](../objects/Timestamp.md) | 否 | 实际结束 |

## 约束与提交

- 效果分类：`internal_write`。
- 认证/上下文：`service`；范围及权限由服务端或Runner取得。
- 请求/动作ID去重与CAS按[统一规则](../CONVENTIONS.md)执行，重复ID不同参数必须冲突。
- 终态与必要事件本地事务提交；外部公开发布另走Tool。
- Run核对提案来源与版本
- Workspace确保真实成果可访问
- CAS写Run终态和相应交付引用
- 发送完整/部分/受阻说明与验证范围，用户审阅状态另存
- 取消/超时遵从COMMON_CONTRACTS；所有引用必须当前权限内、版本可访问。

## 错误、等待、取消

- CAS冲突重读而非覆盖
- 产物不可读不能假交付
- 未决项保持可见

错误对象是 [Failure](../objects/Failure.md)；统一分类：schema_invalid / permission_denied / feature_disabled / revision_conflict / stale_resource / dependency_unavailable / budget_exceeded / deadline_exceeded / cancelled / unknown_effect。实际Runtime需要把业务错误映射到此对象；上述分类不会代替明确failed_phase和恢复提示。

只读可在有界策略内重试；写失败先核对动作账本，效果unknown时禁止盲重试；waiting通过审批决定、用户输入、process.poll或agents.wait推进。取消只停止后续执行，已有效果如实保留。

## 请求示例

示例展示结构；不代表这些示例引用存在。

```json
{
  "proposal_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "expected_run_revision": 0,
  "artifact_manifest_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "proposed_outcome": "succeeded"
}
```

## 成功结构示例

```json
{
  "kind": "ok",
  "payload": {
    "id": "example_001",
    "task_id": "example_001",
    "conversation_id": "example_001",
    "revision": 0,
    "status": "queued",
    "budget": {
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
    "created_at": "2026-10-07T02:00:00Z"
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
| `agent.completion.delivery` | [开发设计](../../../docs/design/components/agent-completion-delivery.md) | `src/uaw/agent/completion/delivery.py` |

[接口机器目录](../../../contracts/interfaces.json) · [统一对象schema](../../../contracts/uaw.schema.json)
