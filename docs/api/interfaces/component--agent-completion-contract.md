# agent.completion.contract

状态：契约0.1，待实现。类别：细分组件私有接口。所属：Agent执行与协作。

语义交付契约的私有阶段输入。

[分类索引](../COMPONENT.md) · [统一规则](../CONVENTIONS.md) · [实际范围](../../implementation/README.md)

## 调用入口

计划Python异步签名：`async def handle(request: InternalAgentCompletionContractRequest, context: TrustedExecutionContext) -> ComponentAgentCompletionContractResult`。所属入口为 `agent.completion.contract`。该签名是契约目标；实际方法定位见对应开发设计，不能从公网/LLM直接调用私有组件。

## 输入

[InternalAgentCompletionContractRequest](../objects/InternalAgentCompletionContractRequest.md)；每个字段的类型、必填性、默认注解、限制和分支见对象页。

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `user_input_refs` | 数组&lt;[Ref](../objects/Ref.md)&gt; | 是 | 原始用户输入及有效补充，解析交付要求的依据。 |
| `task_frame_ref` | [Ref](../objects/Ref.md) | 是 | 当前任务理解，包含原文和明确约束来源。 |
| `proposed_requirements` | 数组&lt;[Requirement](../objects/Requirement.md)&gt; | 是 | 模型提取的候选要求，核对用户原文与政策来源。 |

## 输出

[ComponentAgentCompletionContractResult](../objects/ComponentAgentCompletionContractResult.md) 为完整返回结构。`kind=ok` 的payload是 [Contract](../objects/Contract.md)。`waiting`带wait_ref，其他非成功状态带Failure，不能用空对象假装成功。

| payload字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `goal` | [NonEmptyText](../objects/NonEmptyText.md) | 是 | 目标 |
| `requirements` | 数组&lt;[Requirement](../objects/Requirement.md)&gt; | 是 | 验收条件 |
| `outputs` | 数组&lt;[OutputSpec](../objects/OutputSpec.md)&gt; | 是 | 交付物要求 |
| `version` | [Version](../objects/Version.md) | 是 | 契约版本 |
| `acceptance_required` | [Bool](../objects/Bool.md) | 否 | Task结束是否需用户接受 |

## 约束与提交

- 效果分类：`read`。
- 认证/上下文：`service`；范围及权限由服务端或Runner取得。
- 请求/动作ID去重与CAS按[统一规则](../CONVENTIONS.md)执行，重复ID不同参数必须冲突。
- DeliveryContract追加版本并绑定用户/政策来源。
- 提取原文和用户纠正的必需目标
- 分开硬约束与开放质量标准
- LLM可提出补充验证但不能删必需要求
- 为每项确定可接受成果/证据或明确待澄清
- 取消/超时遵从COMMON_CONTRACTS；所有引用必须当前权限内、版本可访问。

## 错误、等待、取消

- 关键标准冲突返回clarification_required
- 模型自降目标拒绝

错误对象是 [Failure](../objects/Failure.md)；统一分类：schema_invalid / permission_denied / feature_disabled / revision_conflict / stale_resource / dependency_unavailable / budget_exceeded / deadline_exceeded / cancelled / unknown_effect。实际Runtime需要把业务错误映射到此对象；上述分类不会代替明确failed_phase和恢复提示。

只读可在有界策略内重试；写失败先核对动作账本，效果unknown时禁止盲重试；waiting通过审批决定、用户输入、process.poll或agents.wait推进。取消只停止后续执行，已有效果如实保留。

## 请求示例

示例展示结构；不代表这些示例引用存在。

```json
{
  "user_input_refs": [],
  "task_frame_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "proposed_requirements": []
}
```

## 成功结构示例

```json
{
  "kind": "ok",
  "payload": {
    "goal": "example_001",
    "requirements": [],
    "outputs": [],
    "version": "example_001"
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
| `agent.completion.contract` | [开发设计](../../../docs/design/components/agent-completion-contract.md) | `src/uaw/agent/completion/contract.py` |

[接口机器目录](../../../contracts/interfaces.json) · [统一对象schema](../../../contracts/uaw.schema.json)
