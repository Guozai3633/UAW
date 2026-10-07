# agent.definitions.model_intent

状态：契约0.1，待实现。类别：细分组件私有接口。所属：Agent执行与协作。

模型政策必须来自明确用户意图或父政策。

[分类索引](../COMPONENT.md) · [统一规则](../CONVENTIONS.md) · [实际范围](../../implementation/README.md)

## 调用入口

计划Python异步签名：`async def handle(request: ModelPolicyRequest, context: TrustedExecutionContext) -> ComponentAgentDefinitionsModelIntentResult`。所属入口为 `agent.definitions.model_intent`。该签名是契约目标；实际方法定位见对应开发设计，不能从公网/LLM直接调用私有组件。

## 输入

[ModelPolicyRequest](../objects/ModelPolicyRequest.md)；每个字段的类型、必填性、默认注解、限制和分支见对象页。

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `conversation_selection` | [ModelSelection](../objects/ModelSelection.md) | 是 | 会话已记录意图 |
| `parent_policy_ref` | [Ref](../objects/Ref.md) | 否 | 父政策 |
| `explicit_child_request` | [ModelRequest](../objects/ModelRequest.md) | 否 | 子覆盖 |
| `user_source_ref` | [UserInputRef](../objects/UserInputRef.md) | 是 | 真实用户依据 |

## 输出

[ComponentAgentDefinitionsModelIntentResult](../objects/ComponentAgentDefinitionsModelIntentResult.md) 为完整返回结构。`kind=ok` 的payload是 [ResolvedModelPolicy](../objects/ResolvedModelPolicy.md)。`waiting`带wait_ref，其他非成功状态带Failure，不能用空对象假装成功。

| payload字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `id` | [ID](../objects/ID.md) | 是 | 模型政策 |
| `revision` | [Revision](../objects/Revision.md) | 是 | 政策版本 |
| `mode` | enum: `explicit` / `auto` | 是 | 继承已经解析为父政策模式。 |
| `fixed_model_id` | [ID](../objects/ID.md) | 否 | 固定模型 |
| `allowed_model_ids` | 数组&lt;[ID](../objects/ID.md)&gt; | 是 | Auto候选集 |
| `source_input_ref` | [UserInputRef](../objects/UserInputRef.md) | 是 | 明确用户选择 |
| `parent_policy_ref` | [Ref](../objects/Ref.md) | 否 | 继承链 |

## 约束与提交

- 效果分类：`read`。
- 认证/上下文：`service`；范围及权限由服务端或Runner取得。
- 请求/动作ID去重与CAS按[统一规则](../CONVENTIONS.md)执行，重复ID不同参数必须冲突。
- 保存用户模型意图与规范引用，实例创建时再解析实际继承。
- inherit不写死当前型号
- explicit核对用户原文指定并保留原名称
- 通过Model目录精确/登记别名解析可见候选
- 缺失/歧义/不可用返回当前主LLM解释或询问
- 只有用户授权替代或Auto时选择合法范围后重提交
- 取消/超时遵从COMMON_CONTRACTS；所有引用必须当前权限内、版本可访问。

## 错误、等待、取消

- model_not_found不启用
- model_ambiguous不猜
- 未经授权替代拒绝

错误对象是 [Failure](../objects/Failure.md)；统一分类：schema_invalid / permission_denied / feature_disabled / revision_conflict / stale_resource / dependency_unavailable / budget_exceeded / deadline_exceeded / cancelled / unknown_effect。实际Runtime需要把业务错误映射到此对象；上述分类不会代替明确failed_phase和恢复提示。

只读可在有界策略内重试；写失败先核对动作账本，效果unknown时禁止盲重试；waiting通过审批决定、用户输入、process.poll或agents.wait推进。取消只停止后续执行，已有效果如实保留。

## 请求示例

示例展示结构；不代表这些示例引用存在。

```json
{
  "conversation_selection": {
    "mode": "inherit"
  },
  "user_source_ref": {
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
    "id": "example_001",
    "revision": 0,
    "mode": "explicit",
    "allowed_model_ids": [],
    "source_input_ref": {
      "kind": "input",
      "id": "example_001",
      "version": "example_001"
    },
    "fixed_model_id": "example_001"
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
| `agent.definitions.model_intent` | [开发设计](../../../docs/design/components/agent-definitions-model_intent.md) | `src/uaw/agent/definitions/model_intent.py` |

[接口机器目录](../../../contracts/interfaces.json) · [统一对象schema](../../../contracts/uaw.schema.json)
