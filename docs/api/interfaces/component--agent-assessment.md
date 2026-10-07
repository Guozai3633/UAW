# agent.assessment

状态：契约0.1，待实现。类别：细分组件私有接口。所属：Agent执行与协作。

按需执行评估的私有阶段输入。

[分类索引](../COMPONENT.md) · [统一规则](../CONVENTIONS.md) · [实际范围](../../implementation/README.md)

## 调用入口

计划Python异步签名：`async def handle(request: InternalAgentAssessmentRequest, context: TrustedExecutionContext) -> ComponentAgentAssessmentResult`。所属入口为 `agent.assessment`。该签名是契约目标；实际方法定位见对应开发设计，不能从公网/LLM直接调用私有组件。

## 输入

[InternalAgentAssessmentRequest](../objects/InternalAgentAssessmentRequest.md)；每个字段的类型、必填性、默认注解、限制和分支见对象页。

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `task_frame_ref` | [Ref](../objects/Ref.md) | 是 | 当前任务理解，包含原文和明确约束来源。 |
| `capability_snapshot` | [Ref](../objects/Ref.md) | 是 | 当前有效能力及旗标版本，用于缩小候选。 |
| `existing_agent_refs` | 数组&lt;[Ref](../objects/Ref.md)&gt; | 是 | 当前可用实例/角色摘要，避免无必要新增Agent。 |
| `decision_question` | [Text](../objects/Text.md) | 否 | 需要本次复评的具体问题，避免重做全部理解。 |

## 输出

[ComponentAgentAssessmentResult](../objects/ComponentAgentAssessmentResult.md) 为完整返回结构。`kind=ok` 的payload是 [ExecutionAssessment](../objects/ExecutionAssessment.md)。`waiting`带wait_ref，其他非成功状态带Failure，不能用空对象假装成功。

| payload字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `planning` | [PlanningLevel](../objects/PlanningLevel.md) | 是 | 无规划、清单或依赖图 |
| `delegation` | [DelegationMode](../objects/DelegationMode.md) | 是 | 单Agent或父子Agent |
| `parallelism` | [Parallelism](../objects/Parallelism.md) | 是 | 顺序或独立部分并发 |
| `information_state` | [InformationState](../objects/InformationState.md) | 是 | 可以开始、先读材料或澄清 |
| `rationale` | [NonEmptyText](../objects/NonEmptyText.md) | 是 | 判断依据及成本收益 |
| `candidate_agent_refs` | 数组&lt;[Ref](../objects/Ref.md)&gt; | 是 | 可用角色候选 |
| `independent_groups` | 数组&lt;[WorkGroup](../objects/WorkGroup.md)&gt; | 是 | 可独立执行的工作 |
| `reassessment_conditions` | 数组&lt;[NonEmptyText](../objects/NonEmptyText.md)&gt; | 是 | 需要重新判断的条件 |
| `source_frame_ref` | [Ref](../objects/Ref.md) | 是 | 本次理解版本 |
| `decision_status` | [DecisionStatus](../objects/DecisionStatus.md) | 是 | 资料不足时暂定 |
| `parallel_scope` | [ParallelScope](../objects/ParallelScope.md) | 是 | 工具并发与Agent并发分开 |
| `suggested_delegations` | 数组&lt;[SuggestedDelegation](../objects/SuggestedDelegation.md)&gt; | 是 | 建议而非已启动 |

## 约束与提交

- 效果分类：`read`。
- 认证/上下文：`service`；范围及权限由服务端或Runner取得。
- 请求/动作ID去重与CAS按[统一规则](../CONVENTIONS.md)执行，重复ID不同参数必须冲突。
- Assessment是建议记录，不直接创建实例或把全部步骤标记ready。
- 按原文、独立子成果、依赖、风险与可用能力作语义评估
- 分别输出planning_level、delegation、parallelism及信息缺口
- 附可验收子目标和预估协调/等待成本
- Runtime检查预算、最大深度、flag与资源上限
- 证据不足以证明委派收益时保持单Agent，运行中可根据失败/新材料复评
- 取消/超时遵从COMMON_CONTRACTS；所有引用必须当前权限内、版本可访问。

## 错误、等待、取消

- 不支持能力返回capability_gap
- schema错有界修复
- 超预算建议被拒绝并回LLM缩小计划

错误对象是 [Failure](../objects/Failure.md)；统一分类：schema_invalid / permission_denied / feature_disabled / revision_conflict / stale_resource / dependency_unavailable / budget_exceeded / deadline_exceeded / cancelled / unknown_effect。实际Runtime需要把业务错误映射到此对象；上述分类不会代替明确failed_phase和恢复提示。

只读可在有界策略内重试；写失败先核对动作账本，效果unknown时禁止盲重试；waiting通过审批决定、用户输入、process.poll或agents.wait推进。取消只停止后续执行，已有效果如实保留。

## 请求示例

示例展示结构；不代表这些示例引用存在。

```json
{
  "task_frame_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "capability_snapshot": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "existing_agent_refs": []
}
```

## 成功结构示例

```json
{
  "kind": "ok",
  "payload": {
    "planning": "steps",
    "delegation": "single",
    "parallelism": "parallel",
    "information_state": "read_materials",
    "rationale": "先并发只读检索接口与调用方；是否委派需读完材料后再判断。",
    "candidate_agent_refs": [],
    "independent_groups": [],
    "reassessment_conditions": [
      "读取实现和调用方后"
    ],
    "source_frame_ref": {
      "kind": "task_frame",
      "id": "task_api_1",
      "version": "1"
    },
    "decision_status": "provisional",
    "parallel_scope": "tools",
    "suggested_delegations": []
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
| `agent.assessment` | [开发设计](../../../docs/design/components/agent-assessment.md) | `src/uaw/agent/assessment.py` |

[接口机器目录](../../../contracts/interfaces.json) · [统一对象schema](../../../contracts/uaw.schema.json)
