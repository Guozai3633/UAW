# context.selection

状态：契约0.1，待实现。类别：细分组件私有接口。所属：上下文与资料。

互斥分支；所有字段须匹配所选action。

[分类索引](../COMPONENT.md) · [统一规则](../CONVENTIONS.md) · [实际范围](../../implementation/README.md)

## 调用入口

计划Python异步签名：`async def handle(request: InternalContextSelectionRequest, context: TrustedExecutionContext) -> ComponentContextSelectionResult`。所属入口为 `context.selection`。该签名是契约目标；实际方法定位见对应开发设计，不能从公网/LLM直接调用私有组件。

## 输入

[InternalContextSelectionRequest](../objects/InternalContextSelectionRequest.md)；每个字段的类型、必填性、默认注解、限制和分支见对象页。

动作分支：

- [InternalContextSelectionRequestSelect](../objects/InternalContextSelectionRequestSelect.md)
- [InternalContextSelectionRequestAllocate](../objects/InternalContextSelectionRequestAllocate.md)

## 输出

[ComponentContextSelectionResult](../objects/ComponentContextSelectionResult.md) 为完整返回结构。`kind=ok` 的payload是 [InternalContextSelectionOutput](../objects/InternalContextSelectionOutput.md)。`waiting`带wait_ref，其他非成功状态带Failure，不能用空对象假装成功。


## 约束与提交

- 效果分类：`read`。
- 认证/上下文：`service`；范围及权限由服务端或Runner取得。
- 请求/动作ID去重与CAS按[统一规则](../CONVENTIONS.md)执行，重复ID不同参数必须冲突。
- 记录被选/被排除块和原因到ContextManifest，真实用量更新预算估计。
- 先从模型可用窗口扣除输出/工具反馈/必要压缩余量
- 用户原文、硬约束与当前未完成状态优先
- 按来源可信、目标覆盖、时效、成本选择候选
- 大工具结果先分页/筛选，避免用一次压缩解决无限输入
- 剩余缺口转压缩或读取需求，不能静默丢关键条件
- 取消/超时遵从COMMON_CONTRACTS；所有引用必须当前权限内、版本可访问。

## 错误、等待、取消

- 必需内容装不下返回context_insufficient
- 未知tokenizer使用保守估算并报告
- 无关块不补满窗口

错误对象是 [Failure](../objects/Failure.md)；统一分类：schema_invalid / permission_denied / feature_disabled / revision_conflict / stale_resource / dependency_unavailable / budget_exceeded / deadline_exceeded / cancelled / unknown_effect。实际Runtime需要把业务错误映射到此对象；上述分类不会代替明确failed_phase和恢复提示。

只读可在有界策略内重试；写失败先核对动作账本，效果unknown时禁止盲重试；waiting通过审批决定、用户输入、process.poll或agents.wait推进。取消只停止后续执行，已有效果如实保留。

## 请求示例

示例展示结构；不代表这些示例引用存在。

```json
{
  "action": "select",
  "parameters": {
    "candidate_refs": [],
    "purpose": "draft_preview",
    "model_context_limit": 1,
    "output_reserve": 0,
    "tool_reserve": 0
  }
}
```

## 成功结构示例

```json
{
  "kind": "ok",
  "payload": {
    "action": "select",
    "result": {
      "selected_refs": [],
      "omitted_refs": [],
      "allocated_tokens": 0,
      "preserved_refs": []
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
| `context.selection` | [开发设计](../../../docs/design/components/context-selection.md) | `src/uaw/context/selection.py` |

[接口机器目录](../../../contracts/interfaces.json) · [统一对象schema](../../../contracts/uaw.schema.json)
