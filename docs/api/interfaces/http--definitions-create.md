# definitions.create

状态：契约0.1，待实现。类别：用户与管理端 HTTP API。所属：Agent执行与协作。

保存角色。

[分类索引](../HTTP.md) · [统一规则](../CONVENTIONS.md) · [实际范围](../../implementation/README.md)

## 调用入口

`POST /v1/conversations/{conversation_id}/agents`；认证：`user`。

请求体是 `{meta, payload}`；路径ID从path取得，不重复写入payload。OpenAPI记录实际线上字段位置；下方输入对象是服务合成的业务请求。

## 输入

[DefinitionsCreateRequest](../objects/DefinitionsCreateRequest.md)；每个字段的类型、必填性、默认注解、限制和分支见对象页。

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `conversation_id` | [ID](../objects/ID.md) | 是 | 会话 |
| `definitions` | [DefinitionDrafts](../objects/DefinitionDrafts.md) | 是 | 批量草案 |
| `batch_policy` | [BatchPolicy](../objects/BatchPolicy.md) | 是 | atomic或independent |
| `source_input_ref` | [UserInputRef](../objects/UserInputRef.md) | 是 | 用户明确创建依据 |

## 输出

[HttpDefinitionsCreateResult](../objects/HttpDefinitionsCreateResult.md) 为完整返回结构。`kind=ok` 的payload是 [DefinitionBatchResult](../objects/DefinitionBatchResult.md)。`waiting`带wait_ref，其他非成功状态带Failure，不能用空对象假装成功。

| payload字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `batch_policy` | enum: `atomic` / `independent` | 是 | 提交策略 |
| `items` | 数组&lt;[DefinitionItemResult](../objects/DefinitionItemResult.md)&gt; | 是 | 逐项真实结果 |
| `committed_revision` | [Revision](../objects/Revision.md) | 否 | 已提交域修订 |

## 约束与提交

- 效果分类：`internal_write`。
- 认证/上下文：`user`；范围及权限由服务端或Runner取得。
- 请求/动作ID去重与CAS按[统一规则](../CONVENTIONS.md)执行，重复ID不同参数必须冲突。
- 不会启动实例；显式模型缺失返回needs_resolution；会话名唯一；幂等client_definition_key。

## 错误、等待、取消

错误对象是 [Failure](../objects/Failure.md)；统一分类：schema_invalid / permission_denied / feature_disabled / revision_conflict / stale_resource / dependency_unavailable / budget_exceeded / deadline_exceeded / cancelled / unknown_effect。实际Runtime需要把业务错误映射到此对象；上述分类不会代替明确failed_phase和恢复提示。

只读可在有界策略内重试；写失败先核对动作账本，效果unknown时禁止盲重试；waiting通过审批决定、用户输入、process.poll或agents.wait推进。取消只停止后续执行，已有效果如实保留。

## 请求示例

示例展示结构；不代表这些示例引用存在。

```json
{
  "meta": {
    "request_id": "request_001",
    "schema_version": "0.1",
    "expected_revision": 0
  },
  "payload": {
    "definitions": [
      {
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
      }
    ],
    "batch_policy": "atomic",
    "source_input_ref": {
      "kind": "input",
      "id": "example_001",
      "version": "example_001"
    }
  }
}
```

## 成功结构示例

```json
{
  "kind": "ok",
  "payload": {
    "batch_policy": "atomic",
    "items": [
      {
        "client_definition_key": "example_001",
        "status": "created",
        "definition": {
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
        }
      }
    ]
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
| `ui` | [开发设计](../../../docs/design/components/ui.md) | `apps/web/src/features/workspace/` |
| `agent.definitions` | [开发设计](../../../docs/design/components/agent-definitions.md) | `src/uaw/agent/definitions/facade.py` |
| `agent.definitions.validator` | [开发设计](../../../docs/design/components/agent-definitions-validator.md) | `src/uaw/agent/definitions/validator.py` |
| `agent.definitions.model_intent` | [开发设计](../../../docs/design/components/agent-definitions-model_intent.md) | `src/uaw/agent/definitions/model_intent.py` |
| `agent.definitions.repository` | [开发设计](../../../docs/design/components/agent-definitions-repository.md) | `src/uaw/agent/definitions/repository.py` |

[接口机器目录](../../../contracts/interfaces.json) · [统一对象schema](../../../contracts/uaw.schema.json)
