# run.resume.effects

状态：契约0.1，待实现。类别：细分组件私有接口。所属：运行与会话。

Tool未决动作对账的私有阶段输入。

[分类索引](../COMPONENT.md) · [统一规则](../CONVENTIONS.md) · [实际范围](../../implementation/README.md)

## 调用入口

计划Python异步签名：`async def handle(request: InternalRunResumeEffectsRequest, context: TrustedExecutionContext) -> ComponentRunResumeEffectsResult`。所属入口为 `run.resume.effects`。该签名是契约目标；实际方法定位见对应开发设计，不能从公网/LLM直接调用私有组件。

## 输入

[InternalRunResumeEffectsRequest](../objects/InternalRunResumeEffectsRequest.md)；每个字段的类型、必填性、默认注解、限制和分支见对象页。

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `tool_ledger_cursor` | [Cursor](../objects/Cursor.md) | 是 | 检查点处的效果账本位置，用于续接对账。 |
| `pending_action_refs` | 数组&lt;[Ref](../objects/Ref.md)&gt; | 是 | 未确认效果动作，恢复前需查回执。 |
| `deadline` | [Timestamp](../objects/Timestamp.md) | 是 | 绝对UTC截止；重试和子调用不能延长父deadline。 |

## 输出

[ComponentRunResumeEffectsResult](../objects/ComponentRunResumeEffectsResult.md) 为完整返回结构。`kind=ok` 的payload是 [ResumeEffectsResult](../objects/ResumeEffectsResult.md)。`waiting`带wait_ref，其他非成功状态带Failure，不能用空对象假装成功。

| payload字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `confirmed_refs` | 数组&lt;[Ref](../objects/Ref.md)&gt; | 是 | 已对账 |
| `unknown_refs` | 数组&lt;[Ref](../objects/Ref.md)&gt; | 是 | 仍未知 |
| `retryable_action_refs` | 数组&lt;[Ref](../objects/Ref.md)&gt; | 是 | 可安全恢复动作 |

## 约束与提交

- 效果分类：`read`。
- 认证/上下文：`service`；范围及权限由服务端或Runner取得。
- 请求/动作ID去重与CAS按[统一规则](../CONVENTIONS.md)执行，重复ID不同参数必须冲突。
- Run记录对账进度引用，效果权威仍归Tool。
- 向Tool请求pending/unknown列表
- 用原业务键查询真实提供方状态
- 确认完成后记录结果，确认未发生且契约允许才重试
- 无法确定保留未决并阻止相关依赖
- 取消/超时遵从COMMON_CONTRACTS；所有引用必须当前权限内、版本可访问。

## 错误、等待、取消

- provider不可查询返回unresolved_effect
- 回执重复幂等更新

错误对象是 [Failure](../objects/Failure.md)；统一分类：schema_invalid / permission_denied / feature_disabled / revision_conflict / stale_resource / dependency_unavailable / budget_exceeded / deadline_exceeded / cancelled / unknown_effect。实际Runtime需要把业务错误映射到此对象；上述分类不会代替明确failed_phase和恢复提示。

只读可在有界策略内重试；写失败先核对动作账本，效果unknown时禁止盲重试；waiting通过审批决定、用户输入、process.poll或agents.wait推进。取消只停止后续执行，已有效果如实保留。

## 请求示例

示例展示结构；不代表这些示例引用存在。

```json
{
  "tool_ledger_cursor": "example_001",
  "pending_action_refs": [],
  "deadline": "2026-10-07T02:00:00Z"
}
```

## 成功结构示例

```json
{
  "kind": "ok",
  "payload": {
    "confirmed_refs": [],
    "unknown_refs": [],
    "retryable_action_refs": []
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
| `run.resume.effects` | [开发设计](../../../docs/design/components/run-resume-effects.md) | `src/uaw/run/resume/effects.py` |

[接口机器目录](../../../contracts/interfaces.json) · [统一对象schema](../../../contracts/uaw.schema.json)
