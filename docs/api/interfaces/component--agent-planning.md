# agent.planning

状态：契约0.1，待实现。类别：细分组件私有接口。所属：Agent执行与协作。

互斥分支；所有字段须匹配所选action。

[分类索引](../COMPONENT.md) · [统一规则](../CONVENTIONS.md) · [实际范围](../../implementation/README.md)

## 调用入口

计划Python异步签名：`async def handle(request: InternalAgentPlanningRequest, context: TrustedExecutionContext) -> ComponentAgentPlanningResult`。所属入口为 `agent.planning`。该签名是契约目标；实际方法定位见对应开发设计，不能从公网/LLM直接调用私有组件。

## 输入

[InternalAgentPlanningRequest](../objects/InternalAgentPlanningRequest.md)；每个字段的类型、必填性、默认注解、限制和分支见对象页。

动作分支：

- [InternalAgentPlanningRequestPlan](../objects/InternalAgentPlanningRequestPlan.md)
- [InternalAgentPlanningRequestValidate](../objects/InternalAgentPlanningRequestValidate.md)

## 输出

[ComponentAgentPlanningResult](../objects/ComponentAgentPlanningResult.md) 为完整返回结构。`kind=ok` 的payload是 [InternalAgentPlanningOutput](../objects/InternalAgentPlanningOutput.md)。`waiting`带wait_ref，其他非成功状态带Failure，不能用空对象假装成功。


## 约束与提交

- 效果分类：`read`。
- 认证/上下文：`service`；范围及权限由服务端或Runner取得。
- 请求/动作ID去重与CAS按[统一规则](../CONVENTIONS.md)执行，重复ID不同参数必须冲突。
- Agent拥有计划版本；已完成结果保留历史引用，受影响节点变stale。
- 步骤模式记录目标与验收，不强行建依赖图
- DAG模式检查引用、环、依赖完备和输出契约
- 估计所需工具/角色及可用预算，计算资源冲突
- PlanPatch验证已完成节点不变量并计算受影响闭包
- CAS发布新计划版本，Scheduler只消费有效版本
- 取消/超时遵从COMMON_CONTRACTS；所有引用必须当前权限内、版本可访问。

## 错误、等待、取消

- 循环依赖返回cycle_path
- 缺输入返回missing_dependency
- CAS冲突不自动覆盖新用户计划

错误对象是 [Failure](../objects/Failure.md)；统一分类：schema_invalid / permission_denied / feature_disabled / revision_conflict / stale_resource / dependency_unavailable / budget_exceeded / deadline_exceeded / cancelled / unknown_effect。实际Runtime需要把业务错误映射到此对象；上述分类不会代替明确failed_phase和恢复提示。

只读可在有界策略内重试；写失败先核对动作账本，效果unknown时禁止盲重试；waiting通过审批决定、用户输入、process.poll或agents.wait推进。取消只停止后续执行，已有效果如实保留。

## 请求示例

示例展示结构；不代表这些示例引用存在。

```json
{
  "action": "plan",
  "parameters": {
    "planning_level": "steps",
    "node_specs": [],
    "expected_plan_revision": 0,
    "patch": {
      "base_revision": 0,
      "upsert_nodes": [],
      "remove_node_ids": [],
      "reason": "example_001"
    }
  }
}
```

## 成功结构示例

```json
{
  "kind": "ok",
  "payload": {
    "action": "plan",
    "result": {
      "task_id": "example_001",
      "revision": 0,
      "planning": "steps",
      "nodes": [],
      "source_frame_ref": {
        "kind": "web",
        "id": "example_001",
        "version": "example_001"
      },
      "created_at": "2026-10-07T02:00:00Z"
    }
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
| `agent.planning` | [开发设计](../../../docs/design/components/agent-planning.md) | `src/uaw/agent/planning.py` |

[接口机器目录](../../../contracts/interfaces.json) · [统一对象schema](../../../contracts/uaw.schema.json)
