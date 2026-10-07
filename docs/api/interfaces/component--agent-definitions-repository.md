# agent.definitions.repository

状态：契约0.1，待实现。类别：细分组件私有接口。所属：Agent执行与协作。

定义提交与版本的私有阶段输入。

[分类索引](../COMPONENT.md) · [统一规则](../CONVENTIONS.md) · [实际范围](../../implementation/README.md)

## 调用入口

计划Python异步签名：`async def handle(request: InternalAgentDefinitionsRepositoryRequest, context: TrustedExecutionContext) -> ComponentAgentDefinitionsRepositoryResult`。所属入口为 `agent.definitions.repository`。该签名是契约目标；实际方法定位见对应开发设计，不能从公网/LLM直接调用私有组件。

## 输入

[InternalAgentDefinitionsRepositoryRequest](../objects/InternalAgentDefinitionsRepositoryRequest.md)；每个字段的类型、必填性、默认注解、限制和分支见对象页。

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `validated_drafts` | 数组&lt;[Draft](../objects/Draft.md)&gt; | 是 | 经过定义、依赖、权限和模型意图核对的草案。 |
| `batch_policy` | enum: `atomic` / `independent` | 是 | atomic整批提交或independent逐项提交。 |
| `stable_item_keys` | 数组&lt;[Text](../objects/Text.md)&gt; | 是 | 与每个草案位置一一对应的稳定去重键。 |
| `expected_versions` | 映射&lt;string, [Revision](../objects/Revision.md)&gt; | 是 | 每个参与资源的预期修订，不允许缺失应校验的资源。 |

## 输出

[ComponentAgentDefinitionsRepositoryResult](../objects/ComponentAgentDefinitionsRepositoryResult.md) 为完整返回结构。`kind=ok` 的payload是 [DefinitionBatchResult](../objects/DefinitionBatchResult.md)。`waiting`带wait_ref，其他非成功状态带Failure，不能用空对象假装成功。

| payload字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `batch_policy` | enum: `atomic` / `independent` | 是 | 提交策略 |
| `items` | 数组&lt;[DefinitionItemResult](../objects/DefinitionItemResult.md)&gt; | 是 | 逐项真实结果 |
| `committed_revision` | [Revision](../objects/Revision.md) | 否 | 已提交域修订 |

## 约束与提交

- 效果分类：`internal_write`。
- 认证/上下文：`service`；范围及权限由服务端或Runner取得。
- 请求/动作ID去重与CAS按[统一规则](../CONVENTIONS.md)执行，重复ID不同参数必须冲突。
- 同版本hash不可变，定义未执行；查询pending意图防反馈丢失重复create。
- 以主体/会话/请求及项键核对重试参数
- atomic先校验全组并事务提交，independent逐项返回结果
- 新增保持名称唯一，更新CAS追加版本
- 启用项进入可发现集合，未解决草稿不能被调用
- 提交后产生配置变更引用及Run事件
- 取消/超时遵从COMMON_CONTRACTS；所有引用必须当前权限内、版本可访问。

## 错误、等待、取消

- 同键不同参数idempotency_conflict
- CAS失败返回当前diff
- atomic失败不提交任一项

错误对象是 [Failure](../objects/Failure.md)；统一分类：schema_invalid / permission_denied / feature_disabled / revision_conflict / stale_resource / dependency_unavailable / budget_exceeded / deadline_exceeded / cancelled / unknown_effect。实际Runtime需要把业务错误映射到此对象；上述分类不会代替明确failed_phase和恢复提示。

只读可在有界策略内重试；写失败先核对动作账本，效果unknown时禁止盲重试；waiting通过审批决定、用户输入、process.poll或agents.wait推进。取消只停止后续执行，已有效果如实保留。

## 请求示例

示例展示结构；不代表这些示例引用存在。

```json
{
  "validated_drafts": [],
  "batch_policy": "atomic",
  "stable_item_keys": [],
  "expected_versions": {}
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
| `agent.definitions.repository` | [开发设计](../../../docs/design/components/agent-definitions-repository.md) | `src/uaw/agent/definitions/repository.py` |

[接口机器目录](../../../contracts/interfaces.json) · [统一对象schema](../../../contracts/uaw.schema.json)
