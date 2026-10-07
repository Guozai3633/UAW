# agent.collaboration.contract

状态：契约0.1，待实现。类别：细分组件私有接口。所属：Agent执行与协作。

子任务契约的私有阶段输入。

[分类索引](../COMPONENT.md) · [统一规则](../CONVENTIONS.md) · [实际范围](../../implementation/README.md)

## 调用入口

计划Python异步签名：`async def handle(request: InternalAgentCollaborationContractRequest, context: TrustedExecutionContext) -> ComponentAgentCollaborationContractResult`。所属入口为 `agent.collaboration.contract`。该签名是契约目标；实际方法定位见对应开发设计，不能从公网/LLM直接调用私有组件。

## 输入

[InternalAgentCollaborationContractRequest](../objects/InternalAgentCollaborationContractRequest.md)；每个字段的类型、必填性、默认注解、限制和分支见对象页。

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `parent_goal_ref` | [Ref](../objects/Ref.md) | 是 | 父当前理解/要求版本，防止子目标偏离。 |
| `proposed_goal` | [Text](../objects/Text.md) | 是 | 父Agent拟定的有界子目标，待委派契约核对。 |
| `input_refs` | 数组&lt;[Ref](../objects/Ref.md)&gt; | 是 | 授权并固定实际版本的输入集合。 |
| `output_contract` | [Contract](../objects/Contract.md) | 是 | 本分工的目标、必须成果和真实证据标准。 |
| `budget` | [Budget](../objects/Budget.md) | 是 | 任务/分工资源上限，不能超过父预留。 |

## 输出

[ComponentAgentCollaborationContractResult](../objects/ComponentAgentCollaborationContractResult.md) 为完整返回结构。`kind=ok` 的payload是 [DelegationSpec](../objects/DelegationSpec.md)。`waiting`带wait_ref，其他非成功状态带Failure，不能用空对象假装成功。

| payload字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `goal` | [NonEmptyText](../objects/NonEmptyText.md) | 是 | 当前委派目标 |
| `input_refs` | 数组&lt;[Ref](../objects/Ref.md)&gt; | 是 | 授权输入 |
| `definition_ref` | [Ref](../objects/Ref.md) | 否 | 固定角色版本 |
| `output_contract` | [Contract](../objects/Contract.md) | 是 | 子成果验收标准 |
| `budget` | [Budget](../objects/Budget.md) | 是 | 父预算内切分 |
| `read_refs` | 数组&lt;[Ref](../objects/Ref.md)&gt; | 是 | 允许读取范围请求 |
| `write_refs` | 数组&lt;[Ref](../objects/Ref.md)&gt; | 是 | 允许修改范围请求 |
| `creation_key` | [ID](../objects/ID.md) | 是 | 委派幂等键 |

## 约束与提交

- 效果分类：`read`。
- 认证/上下文：`service`；范围及权限由服务端或Runner取得。
- 请求/动作ID去重与CAS按[统一规则](../CONVENTIONS.md)执行，重复ID不同参数必须冲突。
- DelegationSpec固定task/plan与输入版本。
- 说明可独立验收子成果与父目标关系
- 核对必要输入是否已经可读、依赖是否满足
- 计算父权限/角色/产品/委托限制交集
- 将协调/汇总预算算入总额，收益不足保持单Agent
- 取消/超时遵从COMMON_CONTRACTS；所有引用必须当前权限内、版本可访问。

## 错误、等待、取消

- 子目标模糊返回contract_gap
- 额外预算不足不创建实例

错误对象是 [Failure](../objects/Failure.md)；统一分类：schema_invalid / permission_denied / feature_disabled / revision_conflict / stale_resource / dependency_unavailable / budget_exceeded / deadline_exceeded / cancelled / unknown_effect。实际Runtime需要把业务错误映射到此对象；上述分类不会代替明确failed_phase和恢复提示。

只读可在有界策略内重试；写失败先核对动作账本，效果unknown时禁止盲重试；waiting通过审批决定、用户输入、process.poll或agents.wait推进。取消只停止后续执行，已有效果如实保留。

## 请求示例

示例展示结构；不代表这些示例引用存在。

```json
{
  "parent_goal_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "proposed_goal": "example_001",
  "input_refs": [],
  "output_contract": {
    "goal": "example_001",
    "requirements": [],
    "outputs": [],
    "version": "example_001"
  },
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
  }
}
```

## 成功结构示例

```json
{
  "kind": "ok",
  "payload": {
    "goal": "example_001",
    "input_refs": [],
    "output_contract": {
      "goal": "example_001",
      "requirements": [],
      "outputs": [],
      "version": "example_001"
    },
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
    "read_refs": [],
    "write_refs": [],
    "creation_key": "example_001"
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
| `agent.collaboration.contract` | [开发设计](../../../docs/design/components/agent-collaboration-contract.md) | `src/uaw/agent/collaboration/contract.py` |

[接口机器目录](../../../contracts/interfaces.json) · [统一对象schema](../../../contracts/uaw.schema.json)
