# run.approval

状态：契约0.1，待实现。类别：细分组件私有接口。所属：运行与会话。

互斥分支；所有字段须匹配所选action。

[分类索引](../COMPONENT.md) · [统一规则](../CONVENTIONS.md) · [实际范围](../../implementation/README.md)

## 调用入口

计划Python异步签名：`async def handle(request: InternalRunApprovalRequest, context: TrustedExecutionContext) -> ComponentRunApprovalResult`。所属入口为 `run.approval`。该签名是契约目标；实际方法定位见对应开发设计，不能从公网/LLM直接调用私有组件。

## 输入

[InternalRunApprovalRequest](../objects/InternalRunApprovalRequest.md)；每个字段的类型、必填性、默认注解、限制和分支见对象页。

动作分支：

- [InternalRunApprovalRequestRequest](../objects/InternalRunApprovalRequestRequest.md)
- [InternalRunApprovalRequestDecide](../objects/InternalRunApprovalRequestDecide.md)
- [InternalRunApprovalRequestControl](../objects/InternalRunApprovalRequestControl.md)

## 输出

[ComponentRunApprovalResult](../objects/ComponentRunApprovalResult.md) 为完整返回结构。`kind=ok` 的payload是 [InternalRunApprovalOutput](../objects/InternalRunApprovalOutput.md)。`waiting`带wait_ref，其他非成功状态带Failure，不能用空对象假装成功。


## 约束与提交

- 效果分类：`read`。
- 认证/上下文：`service`；范围及权限由服务端或Runner取得。
- 请求/动作ID去重与CAS按[统一规则](../CONVENTIONS.md)执行，重复ID不同参数必须冲突。
- Run审批是权威，Reviewer不能审批自己，拒绝记录不可被换工具绕过。
- 审批绑定主体、动作/参数、资源、期限和政策
- manual等用户，assisted只在预授权范围由独立Reviewer决定，automatic不提示但仍受范围约束
- 明确决定持久化并唤醒相关节点
- 执行前由Tool/Runner复核当前撤销与变化
- steer等控制回执注明生效安全边界和不能取消动作
- 取消/超时遵从COMMON_CONTRACTS；所有引用必须当前权限内、版本可访问。

## 错误、等待、取消

- 无回复/超时不批准
- 参数变化返回approval_stale
- 代审不确定升级用户
- 控制版本冲突返回现态

错误对象是 [Failure](../objects/Failure.md)；统一分类：schema_invalid / permission_denied / feature_disabled / revision_conflict / stale_resource / dependency_unavailable / budget_exceeded / deadline_exceeded / cancelled / unknown_effect。实际Runtime需要把业务错误映射到此对象；上述分类不会代替明确failed_phase和恢复提示。

只读可在有界策略内重试；写失败先核对动作账本，效果unknown时禁止盲重试；waiting通过审批决定、用户输入、process.poll或agents.wait推进。取消只停止后续执行，已有效果如实保留。

## 请求示例

示例展示结构；不代表这些示例引用存在。

```json
{
  "action": "request",
  "parameters": {
    "action_id": "example_001",
    "arguments_hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
    "resource_refs": [],
    "effect": "read",
    "summary": "example_001",
    "expires_at": "2026-10-07T02:00:00Z"
  }
}
```

## 成功结构示例

```json
{
  "kind": "ok",
  "payload": {
    "action": "request",
    "result": {
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
| `run.approval` | [开发设计](../../../docs/design/components/run-approval.md) | `src/uaw/run/approval.py` |

[接口机器目录](../../../contracts/interfaces.json) · [统一对象schema](../../../contracts/uaw.schema.json)
