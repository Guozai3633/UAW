# intent.semantic

状态：契约0.1，待实现。类别：细分组件私有接口。所属：任务理解。

语义解析的私有阶段输入。

[分类索引](../COMPONENT.md) · [统一规则](../CONVENTIONS.md) · [实际范围](../../implementation/README.md)

## 调用入口

计划Python异步签名：`async def handle(request: InternalIntentSemanticRequest, context: TrustedExecutionContext) -> ComponentIntentSemanticResult`。所属入口为 `intent.semantic`。该签名是契约目标；实际方法定位见对应开发设计，不能从公网/LLM直接调用私有组件。

## 输入

[InternalIntentSemanticRequest](../objects/InternalIntentSemanticRequest.md)；每个字段的类型、必填性、默认注解、限制和分支见对象页。

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `input_refs` | 数组&lt;[Ref](../objects/Ref.md)&gt; | 是 | 授权并固定实际版本的输入集合。 |
| `instruction_set_ref` | [Ref](../objects/Ref.md) | 是 | 按来源优先级和作用域解决的指令集合。 |
| `material_refs` | 数组&lt;[Ref](../objects/Ref.md)&gt; | 是 | 任务指定或相关的获准实际材料版本。 |

## 输出

[ComponentIntentSemanticResult](../objects/ComponentIntentSemanticResult.md) 为完整返回结构。`kind=ok` 的payload是 [SemanticParse](../objects/SemanticParse.md)。`waiting`带wait_ref，其他非成功状态带Failure，不能用空对象假装成功。

| payload字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `interpretations` | 数组&lt;[Interpretation](../objects/Interpretation.md)&gt; | 是 | 候选 |
| `requirements` | 数组&lt;[Requirement](../objects/Requirement.md)&gt; | 是 | 要求 |
| `output_specs` | 数组&lt;[OutputSpec](../objects/OutputSpec.md)&gt; | 是 | 成果 |
| `source_refs` | 数组&lt;[Ref](../objects/Ref.md)&gt; | 是 | 来源 |

## 约束与提交

- 效果分类：`read`。
- 认证/上下文：`service`；范围及权限由服务端或Runner取得。
- 请求/动作ID去重与CAS按[统一规则](../CONVENTIONS.md)执行，重复ID不同参数必须冲突。
- 解析结果提交新理解版本；原文不变，重大目标变化向用户显示。
- 读取原文和有效补充，不用AI预览替代用户指令
- 简单任务消费首次主调用中的理解摘要，不强制先独立理解再回答
- 复杂指代/关键缺口需要时才深入理解，明确假设与事实来源
- 将必要理解绑定输入版本并CAS保存，不能为保存摘要追加固定模型调用
- 取消/超时遵从COMMON_CONTRACTS；所有引用必须当前权限内、版本可访问。

## 错误、等待、取消

- 结构错误有界修复
- 目标互相冲突返回ambiguity
- 证据不足不填成确定事实

错误对象是 [Failure](../objects/Failure.md)；统一分类：schema_invalid / permission_denied / feature_disabled / revision_conflict / stale_resource / dependency_unavailable / budget_exceeded / deadline_exceeded / cancelled / unknown_effect。实际Runtime需要把业务错误映射到此对象；上述分类不会代替明确failed_phase和恢复提示。

只读可在有界策略内重试；写失败先核对动作账本，效果unknown时禁止盲重试；waiting通过审批决定、用户输入、process.poll或agents.wait推进。取消只停止后续执行，已有效果如实保留。

## 请求示例

示例展示结构；不代表这些示例引用存在。

```json
{
  "input_refs": [],
  "instruction_set_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "material_refs": []
}
```

## 成功结构示例

```json
{
  "kind": "ok",
  "payload": {
    "interpretations": [],
    "requirements": [],
    "output_specs": [],
    "source_refs": []
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
| `intent.semantic` | [开发设计](../../../docs/design/components/intent-semantic.md) | `src/uaw/intent/semantic.py` |

[接口机器目录](../../../contracts/interfaces.json) · [统一对象schema](../../../contracts/uaw.schema.json)
