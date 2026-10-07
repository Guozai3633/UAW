# tool.invocation.approval

状态：契约0.1，待实现。类别：细分组件私有接口。所属：工具运行。

创建固定动作审批。

[分类索引](../COMPONENT.md) · [统一规则](../CONVENTIONS.md) · [实际范围](../../implementation/README.md)

## 调用入口

计划Python异步签名：`async def handle(request: ApprovalCreateRequest, context: TrustedExecutionContext) -> ComponentToolInvocationApprovalResult`。所属入口为 `tool.invocation.approval`。该签名是契约目标；实际方法定位见对应开发设计，不能从公网/LLM直接调用私有组件。

## 输入

[ApprovalCreateRequest](../objects/ApprovalCreateRequest.md)；每个字段的类型、必填性、默认注解、限制和分支见对象页。

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `action_id` | [ID](../objects/ID.md) | 是 | 动作 |
| `arguments_hash` | [Hash](../objects/Hash.md) | 是 | 参数 |
| `resource_refs` | 数组&lt;[Ref](../objects/Ref.md)&gt; | 是 | 资源 |
| `effect` | [EffectKind](../objects/EffectKind.md) | 是 | 效果 |
| `summary` | [NonEmptyText](../objects/NonEmptyText.md) | 是 | 可读行为 |
| `expires_at` | [Timestamp](../objects/Timestamp.md) | 是 | 截止 |

## 输出

[ComponentToolInvocationApprovalResult](../objects/ComponentToolInvocationApprovalResult.md) 为完整返回结构。`kind=ok` 的payload是 [ApprovalRequest](../objects/ApprovalRequest.md)。`waiting`带wait_ref，其他非成功状态带Failure，不能用空对象假装成功。

| payload字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `id` | [ID](../objects/ID.md) | 是 | 审批 |
| `revision` | [Revision](../objects/Revision.md) | 是 | 审批版本 |
| `action_id` | [ID](../objects/ID.md) | 是 | 动作 |
| `arguments_hash` | [Hash](../objects/Hash.md) | 是 | 规范参数 |
| `resource_refs` | 数组&lt;[Ref](../objects/Ref.md)&gt; | 是 | 预期目标版本 |
| `effect` | [EffectKind](../objects/EffectKind.md) | 是 | 效果 |
| `summary` | [NonEmptyText](../objects/NonEmptyText.md) | 是 | 用户可读动作 |
| `mode` | [ApprovalMode](../objects/ApprovalMode.md) | 是 | 当前政策 |
| `status` | [ApprovalStatus](../objects/ApprovalStatus.md) | 是 | 等待/批准等 |
| `expires_at` | [Timestamp](../objects/Timestamp.md) | 是 | 有效期 |

## 约束与提交

- 效果分类：`read`。
- 认证/上下文：`service`；范围及权限由服务端或Runner取得。
- 请求/动作ID去重与CAS按[统一规则](../CONVENTIONS.md)执行，重复ID不同参数必须冲突。
- Run为审批权威，此节点不自批。
- 向Run提交绑定动作的ApprovalRequest
- 只暂停该动作依赖，其他独立读取可继续
- 等待用户或独立代审的明确回执
- 批准返回ApprovalRef给执行前复核，拒绝交主Agent
- 取消/超时遵从COMMON_CONTRACTS；所有引用必须当前权限内、版本可访问。

## 错误、等待、取消

- 无响应返回waiting不是approved
- 过期返回expired

错误对象是 [Failure](../objects/Failure.md)；统一分类：schema_invalid / permission_denied / feature_disabled / revision_conflict / stale_resource / dependency_unavailable / budget_exceeded / deadline_exceeded / cancelled / unknown_effect。实际Runtime需要把业务错误映射到此对象；上述分类不会代替明确failed_phase和恢复提示。

只读可在有界策略内重试；写失败先核对动作账本，效果unknown时禁止盲重试；waiting通过审批决定、用户输入、process.poll或agents.wait推进。取消只停止后续执行，已有效果如实保留。

## 请求示例

示例展示结构；不代表这些示例引用存在。

```json
{
  "action_id": "example_001",
  "arguments_hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "resource_refs": [],
  "effect": "read",
  "summary": "example_001",
  "expires_at": "2026-10-07T02:00:00Z"
}
```

## 成功结构示例

```json
{
  "kind": "ok",
  "payload": {
    "id": "example_001",
    "revision": 0,
    "action_id": "example_001",
    "arguments_hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
    "resource_refs": [],
    "effect": "read",
    "summary": "example_001",
    "mode": "assisted",
    "status": "pending",
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
| `tool.invocation.approval` | [开发设计](../../../docs/design/components/tool-invocation-approval.md) | `src/uaw/tool/invocation/approval.py` |

[接口机器目录](../../../contracts/interfaces.json) · [统一对象schema](../../../contracts/uaw.schema.json)
