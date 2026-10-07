# IntentRuntime.preview

状态：契约0.1，待实现。类别：Runtime 公共入口。所属：任务理解。

草稿理解提示。

[分类索引](../RUNTIME.md) · [统一规则](../CONVENTIONS.md) · [实际范围](../../implementation/README.md)

## 调用入口

计划Python异步签名：`async def preview(request: IntentPreviewRequest, context: TrustedExecutionContext) -> RuntimeIntentruntimePreviewResult`。所属入口为 `IntentRuntime.preview`。该签名是契约目标；实际方法定位见对应开发设计，不能从公网/LLM直接调用私有组件。

## 输入

[IntentPreviewRequest](../objects/IntentPreviewRequest.md)；每个字段的类型、必填性、默认注解、限制和分支见对象页。

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `conversation_id` | [ID](../objects/ID.md) | 是 | 会话 |
| `draft_revision` | [Revision](../objects/Revision.md) | 是 | 草稿版本 |
| `text` | [Text](../objects/Text.md) | 是 | 原文 |
| `attachment_refs` | 数组&lt;[Ref](../objects/Ref.md)&gt; | 是 | 材料 |

## 输出

[RuntimeIntentruntimePreviewResult](../objects/RuntimeIntentruntimePreviewResult.md) 为完整返回结构。`kind=ok` 的payload是 [DraftPreview](../objects/DraftPreview.md)。`waiting`带wait_ref，其他非成功状态带Failure，不能用空对象假装成功。

| payload字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `draft_revision` | [Revision](../objects/Revision.md) | 是 | 对应草稿 |
| `interpretation` | [Interpretation](../objects/Interpretation.md) | 是 | 提示 |
| `model_config_ref` | [Ref](../objects/Ref.md) | 是 | 实际模型 |
| `expires_at` | [Timestamp](../objects/Timestamp.md) | 是 | 提示有效期 |

## 约束与提交

- 效果分类：`read`。
- 认证/上下文：`service`；范围及权限由服务端或Runner取得。
- 请求/动作ID去重与CAS按[统一规则](../CONVENTIONS.md)执行，重复ID不同参数必须冲突。
- 预览只读，不创建正式任务。

## 错误、等待、取消

错误对象是 [Failure](../objects/Failure.md)；统一分类：schema_invalid / permission_denied / feature_disabled / revision_conflict / stale_resource / dependency_unavailable / budget_exceeded / deadline_exceeded / cancelled / unknown_effect。实际Runtime需要把业务错误映射到此对象；上述分类不会代替明确failed_phase和恢复提示。

只读可在有界策略内重试；写失败先核对动作账本，效果unknown时禁止盲重试；waiting通过审批决定、用户输入、process.poll或agents.wait推进。取消只停止后续执行，已有效果如实保留。

## 请求示例

示例展示结构；不代表这些示例引用存在。

```json
{
  "conversation_id": "example_001",
  "draft_revision": 0,
  "text": "example_001",
  "attachment_refs": []
}
```

## 成功结构示例

```json
{
  "kind": "ok",
  "payload": {
    "draft_revision": 0,
    "interpretation": {
      "goal": "example_001",
      "assumptions": [],
      "source_refs": [],
      "missing_facts": []
    },
    "model_config_ref": {
      "kind": "web",
      "id": "example_001",
      "version": "example_001"
    },
    "expires_at": "2026-10-07T02:00:00Z"
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
| `intent.preview` | [开发设计](../../../docs/design/components/intent-preview.md) | `src/uaw/intent/preview.py` |

[接口机器目录](../../../contracts/interfaces.json) · [统一对象schema](../../../contracts/uaw.schema.json)
