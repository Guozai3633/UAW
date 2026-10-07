# agent.collaboration.handoff

状态：契约0.1，待实现。类别：细分组件私有接口。所属：Agent执行与协作。

可选控制权交接的私有阶段输入。

[分类索引](../COMPONENT.md) · [统一规则](../CONVENTIONS.md) · [实际范围](../../implementation/README.md)

## 调用入口

计划Python异步签名：`async def handle(request: InternalAgentCollaborationHandoffRequest, context: TrustedExecutionContext) -> ComponentAgentCollaborationHandoffResult`。所属入口为 `agent.collaboration.handoff`。该签名是契约目标；实际方法定位见对应开发设计，不能从公网/LLM直接调用私有组件。

## 输入

[InternalAgentCollaborationHandoffRequest](../objects/InternalAgentCollaborationHandoffRequest.md)；每个字段的类型、必填性、默认注解、限制和分支见对象页。

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `from_agent_ref` | [Ref](../objects/Ref.md) | 是 | 移交前当前控制实例，必须持有有效租约。 |
| `to_agent_ref` | [Ref](../objects/Ref.md) | 是 | 同任务树且有匹配角色/权限的目标实例。 |
| `expected_control_revision` | [Revision](../objects/Revision.md) | 是 | 控制租约域CAS版本，防止双控制者。 |
| `unfinished_refs` | 数组&lt;[Ref](../objects/Ref.md)&gt; | 是 | 移交给新控制者的未完工作与待定状态引用。 |

## 输出

[ComponentAgentCollaborationHandoffResult](../objects/ComponentAgentCollaborationHandoffResult.md) 为完整返回结构。`kind=ok` 的payload是 [ControlLease](../objects/ControlLease.md)。`waiting`带wait_ref，其他非成功状态带Failure，不能用空对象假装成功。

| payload字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `id` | [ID](../objects/ID.md) | 是 | 租约ID |
| `holder_ref` | [Ref](../objects/Ref.md) | 是 | 当前控制实例 |
| `resource_ref` | [Ref](../objects/Ref.md) | 是 | 受控任务/节点 |
| `fencing_token` | [Revision](../objects/Revision.md) | 是 | 单调栅栏 |
| `expires_at` | [Timestamp](../objects/Timestamp.md) | 是 | 截止时间 |
| `revision` | [Revision](../objects/Revision.md) | 是 | 控制域版本 |

## 约束与提交

- 效果分类：`read`。
- 认证/上下文：`service`；范围及权限由服务端或Runner取得。
- 请求/动作ID去重与CAS按[统一规则](../CONVENTIONS.md)执行，重复ID不同参数必须冲突。
- Agent拥有唯一ControlLease，Run保存恢复引用。
- 验证目标有完整后续职责和许可模型/权限
- 核对在途与未决动作的归属/对账方案
- 准备最小交接上下文与回转条件
- CAS更新ConversationControlLease并发送交接事件
- 旧控制者之后的过期动作/回复被拒绝
- 取消/超时遵从COMMON_CONTRACTS；所有引用必须当前权限内、版本可访问。

## 错误、等待、取消

- CAS失败保留现持有者
- 循环/次数超限拒绝
- 敏感未决无法处理时等待

错误对象是 [Failure](../objects/Failure.md)；统一分类：schema_invalid / permission_denied / feature_disabled / revision_conflict / stale_resource / dependency_unavailable / budget_exceeded / deadline_exceeded / cancelled / unknown_effect。实际Runtime需要把业务错误映射到此对象；上述分类不会代替明确failed_phase和恢复提示。

只读可在有界策略内重试；写失败先核对动作账本，效果unknown时禁止盲重试；waiting通过审批决定、用户输入、process.poll或agents.wait推进。取消只停止后续执行，已有效果如实保留。

## 请求示例

示例展示结构；不代表这些示例引用存在。

```json
{
  "from_agent_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "to_agent_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "expected_control_revision": 0,
  "unfinished_refs": []
}
```

## 成功结构示例

```json
{
  "kind": "ok",
  "payload": {
    "id": "example_001",
    "holder_ref": {
      "kind": "web",
      "id": "example_001",
      "version": "example_001"
    },
    "resource_ref": {
      "kind": "web",
      "id": "example_001",
      "version": "example_001"
    },
    "fencing_token": 0,
    "expires_at": "2026-10-07T02:00:00Z",
    "revision": 0
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
| `agent.collaboration.handoff` | [开发设计](../../../docs/design/components/agent-collaboration-handoff.md) | `src/uaw/agent/collaboration/handoff.py` |

[接口机器目录](../../../contracts/interfaces.json) · [统一对象schema](../../../contracts/uaw.schema.json)
