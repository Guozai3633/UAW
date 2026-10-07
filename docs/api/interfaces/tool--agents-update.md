# agents.update

状态：契约0.1，待实现。类别：模型可调用工具。所属：Agent执行与协作。

更新当前会话角色。

[分类索引](../TOOL.md) · [统一规则](../CONVENTIONS.md) · [实际范围](../../implementation/README.md)

## 调用入口

LLM提出 `agents.update(arguments)` → ToolRuntime校验/权限/必要审批 → `agent`负责人。ToolRuntime注入可信上下文，业务参数只使用下方输入结构。

## 输入

[ToolAgentsUpdateInput](../objects/ToolAgentsUpdateInput.md)；每个字段的类型、必填性、默认注解、限制和分支见对象页。

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `definition_id` | [ID](../objects/ID.md) | 是 | 角色 |
| `expected_revision` | [Revision](../objects/Revision.md) | 是 | 定义CAS版本 |
| `patch` | [DefinitionPatch](../objects/DefinitionPatch.md) | 是 | 修改 |
| `source_input_ref` | [UserInputRef](../objects/UserInputRef.md) | 是 | 用户依据 |

## 输出

[ToolAgentsUpdateResult](../objects/ToolAgentsUpdateResult.md) 为完整返回结构。`kind=ok` 的payload是 [AgentDefinitionVersion](../objects/AgentDefinitionVersion.md)。`waiting`带wait_ref，其他非成功状态带Failure，不能用空对象假装成功。

| payload字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `definition_id` | [ID](../objects/ID.md) | 是 | 定义ID |
| `revision` | [Revision](../objects/Revision.md) | 是 | 单调版本 |
| `content_hash` | [Hash](../objects/Hash.md) | 是 | 不可变摘要 |
| `owner_id` | [ID](../objects/ID.md) | 是 | 真实用户 |
| `conversation_id` | [ID](../objects/ID.md) | 是 | 绑定会话 |
| `draft` | [AgentDefinitionDraft](../objects/AgentDefinitionDraft.md) | 是 | 保存配置 |
| `status` | enum: `enabled` / `disabled` / `pending_resolution` | 是 | 可调用状态 |
| `source_input_ref` | [UserInputRef](../objects/UserInputRef.md) | 是 | 用户来源 |
| `created_at` | [Timestamp](../objects/Timestamp.md) | 是 | 提交时间 |

## 约束与提交

- 效果分类：`internal_write`。
- 认证/上下文：`agent`；范围及权限由服务端或Runner取得。
- 请求/动作ID去重与CAS按[统一规则](../CONVENTIONS.md)执行，重复ID不同参数必须冲突。


## 错误、等待、取消

错误对象是 [Failure](../objects/Failure.md)；统一分类：schema_invalid / permission_denied / feature_disabled / revision_conflict / stale_resource / dependency_unavailable / budget_exceeded / deadline_exceeded / cancelled / unknown_effect。实际Runtime需要把业务错误映射到此对象；上述分类不会代替明确failed_phase和恢复提示。

只读可在有界策略内重试；写失败先核对动作账本，效果unknown时禁止盲重试；waiting通过审批决定、用户输入、process.poll或agents.wait推进。取消只停止后续执行，已有效果如实保留。

## 请求示例

示例展示结构；不代表这些示例引用存在。

```json
{
  "definition_id": "example_001",
  "expected_revision": 0,
  "patch": {
    "name": "example_001"
  },
  "source_input_ref": {
    "kind": "input",
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
    "definition_id": "example_001",
    "revision": 0,
    "content_hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
    "owner_id": "example_001",
    "conversation_id": "example_001",
    "draft": {
      "client_definition_key": "example_001",
      "name": "example_001",
      "description": "example_001",
      "instructions": "example_001",
      "use_when": [
        "example_001"
      ],
      "avoid_when": [],
      "skill_refs": [],
      "tool_categories": [],
      "input_contract": {
        "goal": "example_001",
        "requirements": [],
        "outputs": [],
        "version": "example_001"
      },
      "output_contract": {
        "goal": "example_001",
        "requirements": [],
        "outputs": [],
        "version": "example_001"
      },
      "model_request": {
        "mode": "inherit"
      }
    },
    "status": "enabled",
    "source_input_ref": {
      "kind": "input",
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
| `agent.definitions.change_service` | [开发设计](../../../docs/design/components/agent-definitions-change_service.md) | `src/uaw/agent/definitions/change_service.py` |
| `agent.definitions.validator` | [开发设计](../../../docs/design/components/agent-definitions-validator.md) | `src/uaw/agent/definitions/validator.py` |

[接口机器目录](../../../contracts/interfaces.json) · [统一对象schema](../../../contracts/uaw.schema.json)
