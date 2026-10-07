# intent.ambiguity

状态：契约0.1，待实现。类别：细分组件私有接口。所属：任务理解。

歧义处理的私有阶段输入。

[分类索引](../COMPONENT.md) · [统一规则](../CONVENTIONS.md) · [实际范围](../../implementation/README.md)

## 调用入口

计划Python异步签名：`async def handle(request: InternalIntentAmbiguityRequest, context: TrustedExecutionContext) -> ComponentIntentAmbiguityResult`。所属入口为 `intent.ambiguity`。该签名是契约目标；实际方法定位见对应开发设计，不能从公网/LLM直接调用私有组件。

## 输入

[InternalIntentAmbiguityRequest](../objects/InternalIntentAmbiguityRequest.md)；每个字段的类型、必填性、默认注解、限制和分支见对象页。

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `interpretations` | 数组&lt;[Interpretation](../objects/Interpretation.md)&gt; | 是 | 有用户原文来源的理解候选，不是虚构新目标。 |
| `impact` | [Impact](../objects/Impact.md) | 是 | 理解错误可能产生的影响，用于决定澄清或可逆探查。 |
| `reversible` | [Bool](../objects/Bool.md) | 是 | 错误动作是否有已知可逆策略；不能等同无风险。 |
| `unresolved` | 数组&lt;[Text](../objects/Text.md)&gt; | 是 | 当前还没有答案的关键问题，不自动当成已解决。 |

## 输出

[ComponentIntentAmbiguityResult](../objects/ComponentIntentAmbiguityResult.md) 为完整返回结构。`kind=ok` 的payload是 [AmbiguityDecision](../objects/AmbiguityDecision.md)。`waiting`带wait_ref，其他非成功状态带Failure，不能用空对象假装成功。

| payload字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `selected` | [Interpretation](../objects/Interpretation.md) | 否 | 可执行理解 |
| `question_item_ref` | [Ref](../objects/Ref.md) | 否 | 待用户回答 |
| `assumptions` | 数组&lt;[NonEmptyText](../objects/NonEmptyText.md)&gt; | 是 | 采用假设 |

## 约束与提交

- 效果分类：`read`。
- 认证/上下文：`service`；范围及权限由服务端或Runner取得。
- 请求/动作ID去重与CAS按[统一规则](../CONVENTIONS.md)执行，重复ID不同参数必须冲突。
- 澄清进入Run InteractionItem，用户回答是新输入；假设保持显式版本。
- 逐项区分非关键表达与影响动作后果的歧义
- 已有来源能够排除候选时回填依据
- 低影响可逆行动带假设开始
- 无法安全选择的关键条件提出一组简短澄清
- 决策随新材料和用户输入复评
- 取消/超时遵从COMMON_CONTRACTS；所有引用必须当前权限内、版本可访问。

## 错误、等待、取消

- 用户未回复只保留waiting，不能视为默认同意
- 澄清回答不匹配原问题返回待解析

错误对象是 [Failure](../objects/Failure.md)；统一分类：schema_invalid / permission_denied / feature_disabled / revision_conflict / stale_resource / dependency_unavailable / budget_exceeded / deadline_exceeded / cancelled / unknown_effect。实际Runtime需要把业务错误映射到此对象；上述分类不会代替明确failed_phase和恢复提示。

只读可在有界策略内重试；写失败先核对动作账本，效果unknown时禁止盲重试；waiting通过审批决定、用户输入、process.poll或agents.wait推进。取消只停止后续执行，已有效果如实保留。

## 请求示例

示例展示结构；不代表这些示例引用存在。

```json
{
  "interpretations": [],
  "impact": "low",
  "reversible": true,
  "unresolved": []
}
```

## 成功结构示例

```json
{
  "kind": "ok",
  "payload": {
    "assumptions": []
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
| `intent.ambiguity` | [开发设计](../../../docs/design/components/intent-ambiguity.md) | `src/uaw/intent/ambiguity.py` |

[接口机器目录](../../../contracts/interfaces.json) · [统一对象schema](../../../contracts/uaw.schema.json)
