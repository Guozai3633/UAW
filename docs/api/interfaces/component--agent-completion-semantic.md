# agent.completion.semantic

状态：契约0.1，待实现。类别：细分组件私有接口。所属：Agent执行与协作。

语义核对的私有阶段输入。

[分类索引](../COMPONENT.md) · [统一规则](../CONVENTIONS.md) · [实际范围](../../implementation/README.md)

## 调用入口

计划Python异步签名：`async def handle(request: InternalAgentCompletionSemanticRequest, context: TrustedExecutionContext) -> ComponentAgentCompletionSemanticResult`。所属入口为 `agent.completion.semantic`。该签名是契约目标；实际方法定位见对应开发设计，不能从公网/LLM直接调用私有组件。

## 输入

[InternalAgentCompletionSemanticRequest](../objects/InternalAgentCompletionSemanticRequest.md)；每个字段的类型、必填性、默认注解、限制和分支见对象页。

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `contract_ref` | [Ref](../objects/Ref.md) | 是 | 当前目标和验收要求的固定版本。 |
| `evidence_refs` | 数组&lt;[Ref](../objects/Ref.md)&gt; | 是 | 实际取得、可读取且与本次要求有关的证据。 |
| `artifact_refs` | 数组&lt;[Ref](../objects/Ref.md)&gt; | 是 | 实际存在、获准且固定版本的成果；不接受虚构路径。 |
| `reviewer_policy` | [Ref](../objects/Ref.md) | 是 | 语义评审方法、模型继承和预算，不替代真实检查。 |

## 输出

[ComponentAgentCompletionSemanticResult](../objects/ComponentAgentCompletionSemanticResult.md) 为完整返回结构。`kind=ok` 的payload是 [VerificationReport](../objects/VerificationReport.md)。`waiting`带wait_ref，其他非成功状态带Failure，不能用空对象假装成功。

| payload字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `id` | [ID](../objects/ID.md) | 是 | 报告 |
| `contract_ref` | [Ref](../objects/Ref.md) | 是 | 交付要求 |
| `target_refs` | 数组&lt;[Ref](../objects/Ref.md)&gt; | 是 | 成果版本 |
| `checks` | 数组&lt;[VerificationCheck](../objects/VerificationCheck.md)&gt; | 是 | 具体检查 |
| `verdicts` | 数组&lt;[RequirementVerdict](../objects/RequirementVerdict.md)&gt; | 是 | 逐要求结果 |
| `outcome` | [Outcome](../objects/Outcome.md) | 是 | 总体结果 |
| `limitations` | 数组&lt;[NonEmptyText](../objects/NonEmptyText.md)&gt; | 是 | 缺口 |
| `reviewer_model_config_ref` | [Ref](../objects/Ref.md) | 否 | 语义评审模型 |
| `created_at` | [Timestamp](../objects/Timestamp.md) | 是 | 生成时间 |

## 约束与提交

- 效果分类：`read`。
- 认证/上下文：`service`；范围及权限由服务端或Runner取得。
- 请求/动作ID去重与CAS按[统一规则](../CONVENTIONS.md)执行，重复ID不同参数必须冲突。
- VerificationReport记录判别方法版本与限制，不直接结束Run。
- 让当前模型对照每项目标与证据
- 区分支持/反驳/未覆盖并列依据
- 缺口可触发获准补查或修订
- 必要独立Reviewer使用隔离上下文且继承模型政策
- 取消/超时遵从COMMON_CONTRACTS；所有引用必须当前权限内、版本可访问。

## 错误、等待、取消

- 缺证据保持unknown
- 裁判受注入指令当数据
- 高不确定需人工反馈

错误对象是 [Failure](../objects/Failure.md)；统一分类：schema_invalid / permission_denied / feature_disabled / revision_conflict / stale_resource / dependency_unavailable / budget_exceeded / deadline_exceeded / cancelled / unknown_effect。实际Runtime需要把业务错误映射到此对象；上述分类不会代替明确failed_phase和恢复提示。

只读可在有界策略内重试；写失败先核对动作账本，效果unknown时禁止盲重试；waiting通过审批决定、用户输入、process.poll或agents.wait推进。取消只停止后续执行，已有效果如实保留。

## 请求示例

示例展示结构；不代表这些示例引用存在。

```json
{
  "contract_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "evidence_refs": [],
  "artifact_refs": [],
  "reviewer_policy": {
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
    "id": "example_001",
    "contract_ref": {
      "kind": "web",
      "id": "example_001",
      "version": "example_001"
    },
    "target_refs": [],
    "checks": [],
    "verdicts": [],
    "outcome": "succeeded",
    "limitations": [],
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
| `agent.completion.semantic` | [开发设计](../../../docs/design/components/agent-completion-semantic.md) | `src/uaw/agent/completion/semantic.py` |

[接口机器目录](../../../contracts/interfaces.json) · [统一对象schema](../../../contracts/uaw.schema.json)
