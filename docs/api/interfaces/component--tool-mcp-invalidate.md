# tool.mcp.invalidate

状态：契约0.1，待实现。类别：细分组件私有接口。所属：工具运行。

变化与撤销的私有阶段输入。

[分类索引](../COMPONENT.md) · [统一规则](../CONVENTIONS.md) · [实际范围](../../implementation/README.md)

## 调用入口

计划Python异步签名：`async def handle(request: InternalToolMcpInvalidateRequest, context: TrustedExecutionContext) -> ComponentToolMcpInvalidateResult`。所属入口为 `tool.mcp.invalidate`。该签名是契约目标；实际方法定位见对应开发设计，不能从公网/LLM直接调用私有组件。

## 输入

[InternalToolMcpInvalidateRequest](../objects/InternalToolMcpInvalidateRequest.md)；每个字段的类型、必填性、默认注解、限制和分支见对象页。

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `provider_ref` | [Ref](../objects/Ref.md) | 是 | 管理员配置且当前可用的固定提供方版本。 |
| `reason` | enum: `revoked` / `expired` / `capability_changed` / `disconnected` | 是 | 明确操作理由；不得用理由文字替代权限/版本校验。 |
| `affected_revision` | [Revision](../objects/Revision.md) | 是 | 发生撤销/能力变化的绑定修订，用于失效传播。 |

## 输出

[ComponentToolMcpInvalidateResult](../objects/ComponentToolMcpInvalidateResult.md) 为完整返回结构。`kind=ok` 的payload是 [Acknowledgement](../objects/Acknowledgement.md)。`waiting`带wait_ref，其他非成功状态带Failure，不能用空对象假装成功。

| payload字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `operation_id` | [ID](../objects/ID.md) | 是 | 受理ID |
| `status` | enum: `accepted` / `unchanged` / `completed` / `pending` | 是 | 确认状态 |
| `related_refs` | 数组&lt;[Ref](../objects/Ref.md)&gt; | 否 | 相关资源 |

## 约束与提交

- 效果分类：`internal_write`。
- 认证/上下文：`service`；范围及权限由服务端或Runner取得。
- 请求/动作ID去重与CAS按[统一规则](../CONVENTIONS.md)执行，重复ID不同参数必须冲突。
- 撤销当前生效，普通版本固定不能绕过。
- 先阻止新敏感调用
- 关闭或标无效旧session
- 让Registry/Discovery/缓存绑定失效
- 已有在途调用按取消能力和效果对账继续跟踪
- 取消/超时遵从COMMON_CONTRACTS；所有引用必须当前权限内、版本可访问。

## 错误、等待、取消

- 关闭失败记录仍在处理但不开放新调用
- 能力变化可重新发现

错误对象是 [Failure](../objects/Failure.md)；统一分类：schema_invalid / permission_denied / feature_disabled / revision_conflict / stale_resource / dependency_unavailable / budget_exceeded / deadline_exceeded / cancelled / unknown_effect。实际Runtime需要把业务错误映射到此对象；上述分类不会代替明确failed_phase和恢复提示。

只读可在有界策略内重试；写失败先核对动作账本，效果unknown时禁止盲重试；waiting通过审批决定、用户输入、process.poll或agents.wait推进。取消只停止后续执行，已有效果如实保留。

## 请求示例

示例展示结构；不代表这些示例引用存在。

```json
{
  "provider_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "reason": "revoked",
  "affected_revision": 0
}
```

## 成功结构示例

```json
{
  "kind": "ok",
  "payload": {
    "operation_id": "example_001",
    "status": "accepted"
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
| `tool.mcp.invalidate` | [开发设计](../../../docs/design/components/tool-mcp-invalidate.md) | `src/uaw/tool/mcp/invalidate.py` |

[接口机器目录](../../../contracts/interfaces.json) · [统一对象schema](../../../contracts/uaw.schema.json)
