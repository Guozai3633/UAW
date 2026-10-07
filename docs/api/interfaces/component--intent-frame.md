# intent.frame

状态：契约0.1，待实现。类别：细分组件私有接口。所属：任务理解。

任务框架的私有阶段输入。

[分类索引](../COMPONENT.md) · [统一规则](../CONVENTIONS.md) · [实际范围](../../implementation/README.md)

## 调用入口

计划Python异步签名：`async def handle(request: InternalIntentFrameRequest, context: TrustedExecutionContext) -> ComponentIntentFrameResult`。所属入口为 `intent.frame`。该签名是契约目标；实际方法定位见对应开发设计，不能从公网/LLM直接调用私有组件。

## 输入

[InternalIntentFrameRequest](../objects/InternalIntentFrameRequest.md)；每个字段的类型、必填性、默认注解、限制和分支见对象页。

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `goal` | [Text](../objects/Text.md) | 是 | 当前目标，必须保留原文与已确认修订的含义。 |
| `constraints` | 数组&lt;[Constraint](../objects/Constraint.md)&gt; | 是 | 有用户/政策来源的任务硬约束。 |
| `output_specs` | 数组&lt;[OutputSpec](../objects/OutputSpec.md)&gt; | 是 | 预期交付类型、用途和是否必需。 |
| `evidence_refs` | 数组&lt;[Ref](../objects/Ref.md)&gt; | 是 | 实际取得、可读取且与本次要求有关的证据。 |
| `expected_revision` | [Revision](../objects/Revision.md) | 是 | 目标域CAS版本；不匹配返回conflict并重新读取。 |

## 输出

[ComponentIntentFrameResult](../objects/ComponentIntentFrameResult.md) 为完整返回结构。`kind=ok` 的payload是 [TaskFrame](../objects/TaskFrame.md)。`waiting`带wait_ref，其他非成功状态带Failure，不能用空对象假装成功。

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

- 效果分类：`read`。
- 认证/上下文：`service`；范围及权限由服务端或Runner取得。
- 请求/动作ID去重与CAS按[统一规则](../CONVENTIONS.md)执行，重复ID不同参数必须冲突。
- Intent是TaskFrame唯一写入者；版本追加，Run记录frame_ref和变更事件。
- 收集语义解析、已定位资源、保留假设和未知项
- 验证硬要求都有用户/政策来源
- 生成TaskFrame候选并比对旧版本
- 用expected_revision提交新版本
- 只标记受变更影响的理解字段，交Agent决定计划失效范围
- 取消/超时遵从COMMON_CONTRACTS；所有引用必须当前权限内、版本可访问。

## 错误、等待、取消

- CAS冲突返回当前frame revision
- 来源缺失不提交伪完整frame
- 重大目标歧义保持pending

错误对象是 [Failure](../objects/Failure.md)；统一分类：schema_invalid / permission_denied / feature_disabled / revision_conflict / stale_resource / dependency_unavailable / budget_exceeded / deadline_exceeded / cancelled / unknown_effect。实际Runtime需要把业务错误映射到此对象；上述分类不会代替明确failed_phase和恢复提示。

只读可在有界策略内重试；写失败先核对动作账本，效果unknown时禁止盲重试；waiting通过审批决定、用户输入、process.poll或agents.wait推进。取消只停止后续执行，已有效果如实保留。

## 请求示例

示例展示结构；不代表这些示例引用存在。

```json
{
  "goal": "example_001",
  "constraints": [],
  "output_specs": [],
  "evidence_refs": [],
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
| `intent.frame` | [开发设计](../../../docs/design/components/intent-frame.md) | `src/uaw/intent/frame.py` |

[接口机器目录](../../../contracts/interfaces.json) · [统一对象schema](../../../contracts/uaw.schema.json)
