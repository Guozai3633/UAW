# agent.definitions.designer

状态：契约0.1，待实现。类别：细分组件私有接口。所属：Agent执行与协作。

角色设计方法的私有阶段输入。

[分类索引](../COMPONENT.md) · [统一规则](../CONVENTIONS.md) · [实际范围](../../implementation/README.md)

## 调用入口

计划Python异步签名：`async def handle(request: InternalAgentDefinitionsDesignerRequest, context: TrustedExecutionContext) -> ComponentAgentDefinitionsDesignerResult`。所属入口为 `agent.definitions.designer`。该签名是契约目标；实际方法定位见对应开发设计，不能从公网/LLM直接调用私有组件。

## 输入

[InternalAgentDefinitionsDesignerRequest](../objects/InternalAgentDefinitionsDesignerRequest.md)；每个字段的类型、必填性、默认注解、限制和分支见对象页。

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `user_input_ref` | [UserInputRef](../objects/UserInputRef.md) | 是 | 当前用户明确要求的原始输入，不是模型推断授权。 |
| `existing_definition_refs` | 数组&lt;[Ref](../objects/Ref.md)&gt; | 是 | 当前会话已保存定义，避免重复职责或同名。 |
| `visible_capabilities` | [Ref](../objects/Ref.md) | 是 | 当前已过滤角色/旗标/主体权限的能力摘要。 |
| `design_method_ref` | [Ref](../objects/Ref.md) | 是 | 主Agent按需加载的精炼角色设计方法。 |

## 输出

[ComponentAgentDefinitionsDesignerResult](../objects/ComponentAgentDefinitionsDesignerResult.md) 为完整返回结构。`kind=ok` 的payload是 [AgentDefinitionDraft](../objects/AgentDefinitionDraft.md)。`waiting`带wait_ref，其他非成功状态带Failure，不能用空对象假装成功。

| payload字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `client_definition_key` | [ID](../objects/ID.md) | 是 | 批量每项稳定幂等键 |
| `name` | string | 是 | 会话内唯一名称 |
| `description` | [NonEmptyText](../objects/NonEmptyText.md) | 是 | 短职责 |
| `instructions` | [NonEmptyText](../objects/NonEmptyText.md) | 是 | 短工作指令 |
| `use_when` | 数组&lt;[NonEmptyText](../objects/NonEmptyText.md)&gt; | 是 | 语义调用条件 |
| `avoid_when` | 数组&lt;[NonEmptyText](../objects/NonEmptyText.md)&gt; | 是 | 排除条件 |
| `skill_refs` | 数组&lt;[Ref](../objects/Ref.md)&gt; | 是 | 获准技能依赖 |
| `tool_categories` | 数组&lt;[ID](../objects/ID.md)&gt; | 是 | 能力类别请求 |
| `input_contract` | [Contract](../objects/Contract.md) | 是 | 必要输入及缺口语义 |
| `output_contract` | [Contract](../objects/Contract.md) | 是 | 子结果验收 |
| `model_request` | [ModelRequest](../objects/ModelRequest.md) | 是 | 模型意图，默认显式填写inherit |

## 约束与提交

- 效果分类：`read`。
- 认证/上下文：`service`；范围及权限由服务端或Runner取得。
- 请求/动作ID去重与CAS按[统一规则](../CONVENTIONS.md)执行，重复ID不同参数必须冲突。
- 只产生待验证草案，Registry提交成功后才宣布已创建。
- 核对用户持久创建/修改要求
- 按需加载短角色设计方法与可用能力
- 当前主模型生成职责/正反调用条件/简短指令与契约
- 未指定模型保留inherit，工具依赖只从真实目录选择
- 关键歧义先澄清，否则调用create/update，不强制独立设计Agent
- 取消/超时遵从COMMON_CONTRACTS；所有引用必须当前权限内、版本可访问。

## 错误、等待、取消

- 未知能力返回dependency_gap
- 模糊持久授权不保存
- 模型不存在保留原意图

错误对象是 [Failure](../objects/Failure.md)；统一分类：schema_invalid / permission_denied / feature_disabled / revision_conflict / stale_resource / dependency_unavailable / budget_exceeded / deadline_exceeded / cancelled / unknown_effect。实际Runtime需要把业务错误映射到此对象；上述分类不会代替明确failed_phase和恢复提示。

只读可在有界策略内重试；写失败先核对动作账本，效果unknown时禁止盲重试；waiting通过审批决定、用户输入、process.poll或agents.wait推进。取消只停止后续执行，已有效果如实保留。

## 请求示例

示例展示结构；不代表这些示例引用存在。

```json
{
  "user_input_ref": {
    "kind": "input",
    "id": "example_001",
    "version": "example_001"
  },
  "existing_definition_refs": [],
  "visible_capabilities": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "design_method_ref": {
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
| `agent.definitions.designer` | [开发设计](../../../docs/design/components/agent-definitions-designer.md) | `src/uaw/agent/definitions/designer.py` |

[接口机器目录](../../../contracts/interfaces.json) · [统一对象schema](../../../contracts/uaw.schema.json)
