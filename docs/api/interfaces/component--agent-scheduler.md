# agent.scheduler

状态：契约0.1，待实现。类别：细分组件私有接口。所属：Agent执行与协作。

节点与资源调度的私有阶段输入。

[分类索引](../COMPONENT.md) · [统一规则](../CONVENTIONS.md) · [实际范围](../../implementation/README.md)

## 调用入口

计划Python异步签名：`async def handle(request: InternalAgentSchedulerRequest, context: TrustedExecutionContext) -> ComponentAgentSchedulerResult`。所属入口为 `agent.scheduler`。该签名是契约目标；实际方法定位见对应开发设计，不能从公网/LLM直接调用私有组件。

## 输入

[InternalAgentSchedulerRequest](../objects/InternalAgentSchedulerRequest.md)；每个字段的类型、必填性、默认注解、限制和分支见对象页。

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `plan_ref` | [Ref](../objects/Ref.md) | 是 | 已校验、已提交的计划修订，不是未接受建议。 |
| `node_states` | 映射&lt;string, [State](../objects/State.md)&gt; | 是 | 当前计划版本每个节点的执行状态。 |
| `available_resources` | [ResourceSnapshot](../objects/ResourceSnapshot.md) | 是 | 当前可用资源快照；实际调度仍原子预留。 |
| `expected_revision` | [Revision](../objects/Revision.md) | 是 | 目标域CAS版本；不匹配返回conflict并重新读取。 |

## 输出

[ComponentAgentSchedulerResult](../objects/ComponentAgentSchedulerResult.md) 为完整返回结构。`kind=ok` 的payload是 [SchedulerResult](../objects/SchedulerResult.md)。`waiting`带wait_ref，其他非成功状态带Failure，不能用空对象假装成功。

| payload字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `ready_node_ids` | 数组&lt;[ID](../objects/ID.md)&gt; | 是 | 可执行 |
| `blocked_node_ids` | 数组&lt;[ID](../objects/ID.md)&gt; | 是 | 受阻 |
| `reserved_refs` | 数组&lt;[Ref](../objects/Ref.md)&gt; | 是 | 实际预留 |

## 约束与提交

- 效果分类：`read`。
- 认证/上下文：`service`；范围及权限由服务端或Runner取得。
- 请求/动作ID去重与CAS按[统一规则](../CONVENTIONS.md)执行，重复ID不同参数必须冲突。
- 领用与预留使用一致提交或可恢复分配意图；完成提交携带node attempt和lease版本。
- 找依赖已满足且结果版本有效的节点
- 核对权限、deadline、工作区写冲突与总预算
- 按就绪节点与受控优先级预留资源并取得租约
- 选单Agent步骤、并发工具或子实例执行，不把节点强制映射Agent
- 完成/失败后重新计算就绪集合并触发Join条件
- 取消/超时遵从COMMON_CONTRACTS；所有引用必须当前权限内、版本可访问。

## 错误、等待、取消

- 资源不足返回queued且等待有界
- 依赖failed/stale阻止调度
- 过期租约完成回执不能覆盖新attempt

错误对象是 [Failure](../objects/Failure.md)；统一分类：schema_invalid / permission_denied / feature_disabled / revision_conflict / stale_resource / dependency_unavailable / budget_exceeded / deadline_exceeded / cancelled / unknown_effect。实际Runtime需要把业务错误映射到此对象；上述分类不会代替明确failed_phase和恢复提示。

只读可在有界策略内重试；写失败先核对动作账本，效果unknown时禁止盲重试；waiting通过审批决定、用户输入、process.poll或agents.wait推进。取消只停止后续执行，已有效果如实保留。

## 请求示例

示例展示结构；不代表这些示例引用存在。

```json
{
  "plan_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "node_states": {},
  "available_resources": {
    "revision": 0,
    "available": {
      "input_tokens": 0,
      "output_tokens": 0,
      "model_calls": 0,
      "tool_calls": 0,
      "child_agents": 0,
      "wall_time_ms": 0,
      "money": "0",
      "currency": "CNY"
    },
    "active_leases": []
  },
  "expected_revision": 0
}
```

## 成功结构示例

```json
{
  "kind": "ok",
  "payload": {
    "ready_node_ids": [],
    "blocked_node_ids": [],
    "reserved_refs": []
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
| `agent.scheduler` | [开发设计](../../../docs/design/components/agent-scheduler.md) | `src/uaw/agent/scheduler.py` |

[接口机器目录](../../../contracts/interfaces.json) · [统一对象schema](../../../contracts/uaw.schema.json)
