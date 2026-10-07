# agents.invoke

状态：契约0.1，待实现。类别：模型可调用工具。所属：Agent执行与协作。

创建隔离实例执行当前有界分工。

[分类索引](../TOOL.md) · [统一规则](../CONVENTIONS.md) · [实际范围](../../implementation/README.md)

## 调用入口

LLM提出 `agents.invoke(arguments)` → ToolRuntime校验/权限/必要审批 → `agent`负责人。ToolRuntime注入可信上下文，业务参数只使用下方输入结构。

## 输入

[ToolAgentsInvokeInput](../objects/ToolAgentsInvokeInput.md)；每个字段的类型、必填性、默认注解、限制和分支见对象页。

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `delegation` | [DelegationSpec](../objects/DelegationSpec.md) | 是 | 目标、资料、成果、预算 |

## 输出

[ToolAgentsInvokeResult](../objects/ToolAgentsInvokeResult.md) 为完整返回结构。`kind=ok` 的payload是 [AgentInstance](../objects/AgentInstance.md)。`waiting`带wait_ref，其他非成功状态带Failure，不能用空对象假装成功。

| payload字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `id` | [ID](../objects/ID.md) | 是 | 实例ID |
| `run_id` | [ID](../objects/ID.md) | 是 | 所属运行 |
| `parent_agent_ref` | [Ref](../objects/Ref.md) | 否 | 根实例无父 |
| `definition_ref` | [Ref](../objects/Ref.md) | 否 | 使用的角色版本 |
| `delegation_ref` | [Ref](../objects/Ref.md) | 否 | 子实例的委派契约 |
| `status` | [State](../objects/State.md) | 是 | 实例状态 |
| `model_policy_ref` | [Ref](../objects/Ref.md) | 是 | 实际继承或覆盖政策 |
| `capability_policy_ref` | [Ref](../objects/Ref.md) | 是 | 有效权限交集 |
| `context_epoch` | [Revision](../objects/Revision.md) | 是 | 上下文纪元 |
| `workspace_ref` | [Ref](../objects/Ref.md) | 否 | 需要文件操作时绑定 |
| `result_ref` | [Ref](../objects/Ref.md) | 否 | 终态结果 |
| `revision` | [Revision](../objects/Revision.md) | 是 | 实例版本 |

## 约束与提交

- 效果分类：`internal_write`。
- 认证/上下文：`agent`；范围及权限由服务端或Runner取得。
- 请求/动作ID去重与CAS按[统一规则](../CONVENTIONS.md)执行，重复ID不同参数必须冲突。
- 调用是当前主Agent语义决定；创建角色不自动invoke；不做独立性成立不了的并发。

## 错误、等待、取消

错误对象是 [Failure](../objects/Failure.md)；统一分类：schema_invalid / permission_denied / feature_disabled / revision_conflict / stale_resource / dependency_unavailable / budget_exceeded / deadline_exceeded / cancelled / unknown_effect。实际Runtime需要把业务错误映射到此对象；上述分类不会代替明确failed_phase和恢复提示。

只读可在有界策略内重试；写失败先核对动作账本，效果unknown时禁止盲重试；waiting通过审批决定、用户输入、process.poll或agents.wait推进。取消只停止后续执行，已有效果如实保留。

## 请求示例

示例展示结构；不代表这些示例引用存在。

```json
{
  "delegation": {
    "goal": "核对本次API修改是否影响已有调用方",
    "input_refs": [
      {
        "kind": "workspace",
        "id": "workspace_main",
        "version": "tree_7"
      }
    ],
    "definition_ref": {
      "kind": "agent_definition",
      "id": "agent_api_reviewer",
      "version": "2"
    },
    "output_contract": {
      "goal": "核对API兼容性并交付证据",
      "requirements": [
        {
          "id": "req_compatibility",
          "text": "说明兼容风险并引用调用方证据",
          "mandatory": true,
          "source_refs": [
            {
              "kind": "input",
              "id": "input_create_roles",
              "version": "1"
            }
          ]
        }
      ],
      "outputs": [
        {
          "id": "out_report",
          "kind": "markdown",
          "description": "含证据的检查报告",
          "required": true
        }
      ],
      "version": "1"
    },
    "budget": {
      "limits": {
        "input_tokens": 60000,
        "output_tokens": 12000,
        "model_calls": 12,
        "tool_calls": 30,
        "child_agents": 0,
        "wall_time_ms": 600000,
        "money": "10.00",
        "currency": "CNY"
      },
      "max_steps": 20,
      "max_depth": 0,
      "deadline": "2026-10-07T02:10:00Z"
    },
    "read_refs": [
      {
        "kind": "workspace",
        "id": "workspace_main",
        "version": "tree_7"
      }
    ],
    "write_refs": [],
    "creation_key": "review_api_change_7"
  }
}
```

## 成功结构示例

```json
{
  "kind": "ok",
  "payload": {
    "id": "example_001",
    "run_id": "example_001",
    "status": "pending",
    "model_policy_ref": {
      "kind": "web",
      "id": "example_001",
      "version": "example_001"
    },
    "capability_policy_ref": {
      "kind": "web",
      "id": "example_001",
      "version": "example_001"
    },
    "context_epoch": 0,
    "revision": 0
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
| `agent.collaboration.contract` | [开发设计](../../../docs/design/components/agent-collaboration-contract.md) | `src/uaw/agent/collaboration/contract.py` |
| `agent.factory` | [开发设计](../../../docs/design/components/agent-factory.md) | `src/uaw/agent/factory.py` |
| `agent.collaboration.instance` | [开发设计](../../../docs/design/components/agent-collaboration-instance.md) | `src/uaw/agent/collaboration/instance.py` |

[接口机器目录](../../../contracts/interfaces.json) · [统一对象schema](../../../contracts/uaw.schema.json)
