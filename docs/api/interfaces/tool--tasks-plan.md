# tasks.plan

状态：契约0.1，待实现。类别：模型可调用工具。所属：Agent执行与协作。

创建/修改执行计划。

[分类索引](../TOOL.md) · [统一规则](../CONVENTIONS.md) · [实际范围](../../implementation/README.md)

## 调用入口

LLM提出 `tasks.plan(arguments)` → ToolRuntime校验/权限/必要审批 → `agent`负责人。ToolRuntime注入可信上下文，业务参数只使用下方输入结构。

## 输入

[ToolTasksPlanInput](../objects/ToolTasksPlanInput.md)；每个字段的类型、必填性、默认注解、限制和分支见对象页。

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `planning_level` | [GraphPlanningLevel](../objects/GraphPlanningLevel.md) | 是 | steps或dag |
| `node_specs` | 数组&lt;[NodeSpec](../objects/NodeSpec.md)&gt; | 是 | 完整初始图 |
| `patch` | [PlanPatch](../objects/PlanPatch.md) | 否 | 增量修改 |
| `expected_plan_revision` | [Revision](../objects/Revision.md) | 是 | 0创建 |

## 输出

[ToolTasksPlanResult](../objects/ToolTasksPlanResult.md) 为完整返回结构。`kind=ok` 的payload是 [TaskGraph](../objects/TaskGraph.md)。`waiting`带wait_ref，其他非成功状态带Failure，不能用空对象假装成功。

| payload字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `task_id` | [ID](../objects/ID.md) | 是 | 所属任务 |
| `revision` | [Revision](../objects/Revision.md) | 是 | 计划版本 |
| `planning` | enum: `steps` / `dag` | 是 | 图仅用于步骤清单或DAG。 |
| `nodes` | 数组&lt;[NodeSpec](../objects/NodeSpec.md)&gt; | 是 | 完整节点集合 |
| `source_frame_ref` | [Ref](../objects/Ref.md) | 是 | 目标理解版本 |
| `created_at` | [Timestamp](../objects/Timestamp.md) | 是 | 提交时间 |

## 约束与提交

- 效果分类：`internal_write`。
- 认证/上下文：`agent`；范围及权限由服务端或Runner取得。
- 请求/动作ID去重与CAS按[统一规则](../CONVENTIONS.md)执行，重复ID不同参数必须冲突。
- patch与非空node_specs互斥；硬依赖校验由代码；不自动invoke。

## 错误、等待、取消

错误对象是 [Failure](../objects/Failure.md)；统一分类：schema_invalid / permission_denied / feature_disabled / revision_conflict / stale_resource / dependency_unavailable / budget_exceeded / deadline_exceeded / cancelled / unknown_effect。实际Runtime需要把业务错误映射到此对象；上述分类不会代替明确failed_phase和恢复提示。

只读可在有界策略内重试；写失败先核对动作账本，效果unknown时禁止盲重试；waiting通过审批决定、用户输入、process.poll或agents.wait推进。取消只停止后续执行，已有效果如实保留。

## 请求示例

示例展示结构；不代表这些示例引用存在。

```json
{
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
```

## 成功结构示例

```json
{
  "kind": "ok",
  "payload": {
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
| `agent.scheduler` | [开发设计](../../../docs/design/components/agent-scheduler.md) | `src/uaw/agent/scheduler.py` |

[接口机器目录](../../../contracts/interfaces.json) · [统一对象schema](../../../contracts/uaw.schema.json)
