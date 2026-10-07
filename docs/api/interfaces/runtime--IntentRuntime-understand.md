# IntentRuntime.understand

状态：有来源的理解协议已实现；真实模型语义质量待验收。类别：Runtime 公共入口。所属：任务理解。

首次理解，可复用主Agent同次输出。

[分类索引](../RUNTIME.md) · [统一规则](../CONVENTIONS.md) · [实际范围](../../implementation/README.md)

## 调用入口

计划Python异步签名：`async def understand(request: UnderstandingRequest, context: TrustedExecutionContext) -> RuntimeIntentruntimeUnderstandResult`。所属入口为 `IntentRuntime.understand`。该签名是契约目标；实际方法定位见对应开发设计，不能从公网/LLM直接调用私有组件。

## 输入

[UnderstandingRequest](../objects/UnderstandingRequest.md)；每个字段的类型、必填性、默认注解、限制和分支见对象页。

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `original_input_ref` | [UserInputRef](../objects/UserInputRef.md) | 是 | 原文 |
| `user_patch_refs` | 数组&lt;[Ref](../objects/Ref.md)&gt; | 是 | 补充 |
| `material_refs` | 数组&lt;[Ref](../objects/Ref.md)&gt; | 是 | 资料 |
| `expected_revision` | [Revision](../objects/Revision.md) | 是 | 理解CAS |

## 输出

[RuntimeIntentruntimeUnderstandResult](../objects/RuntimeIntentruntimeUnderstandResult.md) 为完整返回结构。`kind=ok` 的payload是 [TaskFrame](../objects/TaskFrame.md)。`waiting`带wait_ref，其他非成功状态带Failure，不能用空对象假装成功。

| payload字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `task_id` | [ID](../objects/ID.md) | 是 | 关联任务 |
| `revision` | [Revision](../objects/Revision.md) | 是 | 当前理解版本 |
| `original_input_ref` | [UserInputRef](../objects/UserInputRef.md) | 是 | 原始用户输入 |
| `patch_refs` | 数组&lt;[Ref](../objects/Ref.md)&gt; | 是 | 运行中追加要求 |
| `goal` | string | 是 | 本轮以完整原文及追加要求作为任务基准；AI摘要单独放summary。 |
| `constraints` | 数组&lt;[Constraint](../objects/Constraint.md)&gt; | 是 | 约束及来源 |
| `output_specs` | 数组&lt;[OutputSpec](../objects/OutputSpec.md)&gt; | 是 | 成果要求 |
| `assumptions` | 数组&lt;[NonEmptyText](../objects/NonEmptyText.md)&gt; | 是 | 明确标记的假设 |
| `unresolved` | 数组&lt;[NonEmptyText](../objects/NonEmptyText.md)&gt; | 是 | 未解问题 |
| `evidence_refs` | 数组&lt;[Ref](../objects/Ref.md)&gt; | 是 | 已读取材料 |
| `created_at` | [Timestamp](../objects/Timestamp.md) | 是 | 版本提交时间 |
| `summary` | [NonEmptyText](../objects/NonEmptyText.md) | 否 | AI理解的提示摘要，不授权动作、不替代完整原文。 |
| `input_revision` | [Revision](../objects/Revision.md) | 否 | 生成时的Run输入集合版本；旧理解不得覆盖新输入。 |
| `semantic_parse_ref` | [Ref](../objects/Ref.md) | 否 | 有界模型提案及来源位置，保留模型回执。 |

## 约束与提交

- 效果分类：`internal_write`。
- 认证/上下文：`service`；范围及权限由服务端或Runner取得。
- 请求/动作ID去重与CAS按[统一规则](../CONVENTIONS.md)执行，重复ID不同参数必须冲突。


## 错误、等待、取消

错误对象是 [Failure](../objects/Failure.md)；统一分类：schema_invalid / permission_denied / feature_disabled / revision_conflict / stale_resource / dependency_unavailable / budget_exceeded / deadline_exceeded / cancelled / unknown_effect。实际Runtime需要把业务错误映射到此对象；上述分类不会代替明确failed_phase和恢复提示。

只读可在有界策略内重试；写失败先核对动作账本，效果unknown时禁止盲重试；waiting通过审批决定、用户输入、process.poll或agents.wait推进。取消只停止后续执行，已有效果如实保留。

## 请求示例

示例展示结构；不代表这些示例引用存在。

```json
{
  "original_input_ref": {
    "kind": "input",
    "id": "example_001",
    "version": "example_001"
  },
  "user_patch_refs": [],
  "material_refs": [],
  "expected_revision": 0
}
```

## 成功结构示例

```json
{
  "kind": "ok",
  "payload": {
    "task_id": "example_001",
    "revision": 0,
    "original_input_ref": {
      "kind": "input",
      "id": "example_001",
      "version": "example_001"
    },
    "patch_refs": [],
    "goal": "example_001",
    "constraints": [],
    "output_specs": [],
    "assumptions": [],
    "unresolved": [],
    "evidence_refs": [],
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
| `intent` | [开发设计](../../../docs/design/modules/intent.md) | `src/uaw/intent/facade.py` |
| `intent.original` | [开发设计](../../../docs/design/components/intent-original.md) | `src/uaw/intent/original.py` |
| `intent.semantic` | [开发设计](../../../docs/design/components/intent-semantic.md) | `src/uaw/intent/semantic.py` |
| `intent.frame` | [开发设计](../../../docs/design/components/intent-frame.md) | `src/uaw/intent/frame.py` |

[接口机器目录](../../../contracts/interfaces.json) · [统一对象schema](../../../contracts/uaw.schema.json)
