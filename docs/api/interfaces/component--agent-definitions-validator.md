# agent.definitions.validator

状态：契约0.1，待实现。类别：细分组件私有接口。所属：Agent执行与协作。

定义与授权校验的私有阶段输入。

[分类索引](../COMPONENT.md) · [统一规则](../CONVENTIONS.md) · [实际范围](../../implementation/README.md)

## 调用入口

计划Python异步签名：`async def handle(request: InternalAgentDefinitionsValidatorRequest, context: TrustedExecutionContext) -> ComponentAgentDefinitionsValidatorResult`。所属入口为 `agent.definitions.validator`。该签名是契约目标；实际方法定位见对应开发设计，不能从公网/LLM直接调用私有组件。

## 输入

[InternalAgentDefinitionsValidatorRequest](../objects/InternalAgentDefinitionsValidatorRequest.md)；每个字段的类型、必填性、默认注解、限制和分支见对象页。

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `draft` | [AgentDefinitionDraft](../objects/AgentDefinitionDraft.md) | 是 | 待校验草案，不是已授权可运行实例。 |
| `user_source_ref` | [UserInputRef](../objects/UserInputRef.md) | 是 | 授权/创建/模型覆盖来源，必须是真实用户行为。 |
| `effective_scope` | [Scope](../objects/Scope.md) | 是 | 父、角色、产品、设备权限求交后的真实范围。 |
| `existing_names` | 数组&lt;[Text](../objects/Text.md)&gt; | 是 | 已占用角色名称，按规范化唯一规则比对。 |

## 输出

[ComponentAgentDefinitionsValidatorResult](../objects/ComponentAgentDefinitionsValidatorResult.md) 为完整返回结构。`kind=ok` 的payload是 [ValidationReport](../objects/ValidationReport.md)。`waiting`带wait_ref，其他非成功状态带Failure，不能用空对象假装成功。

| payload字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `valid` | [Bool](../objects/Bool.md) | 是 | 是否通过 |
| `normalized_ref` | [Ref](../objects/Ref.md) | 否 | 规范化对象 |
| `violations` | 数组&lt;[ValidationIssue](../objects/ValidationIssue.md)&gt; | 是 | 问题 |
| `evidence_refs` | 数组&lt;[Ref](../objects/Ref.md)&gt; | 是 | 依据 |

## 约束与提交

- 效果分类：`read`。
- 认证/上下文：`service`；范围及权限由服务端或Runner取得。
- 请求/动作ID去重与CAS按[统一规则](../CONVENTIONS.md)执行，重复ID不同参数必须冲突。
- ValidatedDraft不是enabled定义，必须交Repository提交。
- 服务端核对owner/conversation及真实用户授权
- 检查名称唯一、必需职责/契约与指令长度范围
- 检查可见Skill/tool类别和委派边界
- 新权限只能请求当前有效交集，越界作为阻碍项反馈
- 批量依赖先整组验证
- 取消/超时遵从COMMON_CONTRACTS；所有引用必须当前权限内、版本可访问。

## 错误、等待、取消

- 重名返回definition_conflict
- 依赖缺失返回dependency_missing
- 来源不足返回authorization_gap

错误对象是 [Failure](../objects/Failure.md)；统一分类：schema_invalid / permission_denied / feature_disabled / revision_conflict / stale_resource / dependency_unavailable / budget_exceeded / deadline_exceeded / cancelled / unknown_effect。实际Runtime需要把业务错误映射到此对象；上述分类不会代替明确failed_phase和恢复提示。

只读可在有界策略内重试；写失败先核对动作账本，效果unknown时禁止盲重试；waiting通过审批决定、用户输入、process.poll或agents.wait推进。取消只停止后续执行，已有效果如实保留。

## 请求示例

示例展示结构；不代表这些示例引用存在。

```json
{
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
  "user_source_ref": {
    "kind": "input",
    "id": "example_001",
    "version": "example_001"
  },
  "effective_scope": {
    "principal_id": "example_001"
  },
  "existing_names": []
}
```

## 成功结构示例

```json
{
  "kind": "ok",
  "payload": {
    "valid": true,
    "violations": [],
    "evidence_refs": []
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
| `agent.definitions.validator` | [开发设计](../../../docs/design/components/agent-definitions-validator.md) | `src/uaw/agent/definitions/validator.py` |

[接口机器目录](../../../contracts/interfaces.json) · [统一对象schema](../../../contracts/uaw.schema.json)
