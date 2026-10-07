# agent.collaboration.join

状态：契约0.1，待实现。类别：细分组件私有接口。所属：Agent执行与协作。

收集并核对依赖版本再归并。

[分类索引](../COMPONENT.md) · [统一规则](../CONVENTIONS.md) · [实际范围](../../implementation/README.md)

## 调用入口

计划Python异步签名：`async def handle(request: JoinRequest, context: TrustedExecutionContext) -> ComponentAgentCollaborationJoinResult`。所属入口为 `agent.collaboration.join`。该签名是契约目标；实际方法定位见对应开发设计，不能从公网/LLM直接调用私有组件。

## 输入

[JoinRequest](../objects/JoinRequest.md)；每个字段的类型、必填性、默认注解、限制和分支见对象页。

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `required_result_refs` | 数组&lt;[Ref](../objects/Ref.md)&gt; | 是 | 子结果 |
| `expected_task_revision` | [Revision](../objects/Revision.md) | 是 | 任务版本 |
| `reducer_spec` | [Ref](../objects/Ref.md) | 是 | 归并方法 |

## 输出

[ComponentAgentCollaborationJoinResult](../objects/ComponentAgentCollaborationJoinResult.md) 为完整返回结构。`kind=ok` 的payload是 [AgentResult](../objects/AgentResult.md)。`waiting`带wait_ref，其他非成功状态带Failure，不能用空对象假装成功。

| payload字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `agent_ref` | [Ref](../objects/Ref.md) | 是 | 完成实例版本 |
| `outcome` | [Outcome](../objects/Outcome.md) | 是 | 真实结果 |
| `summary` | [Text](../objects/Text.md) | 是 | 结果摘要 |
| `output_refs` | 数组&lt;[Ref](../objects/Ref.md)&gt; | 是 | 交付引用 |
| `verification_refs` | 数组&lt;[Ref](../objects/Ref.md)&gt; | 是 | 核验证据 |
| `limitations` | 数组&lt;[NonEmptyText](../objects/NonEmptyText.md)&gt; | 是 | 未完成项 |
| `usage_ref` | [Ref](../objects/Ref.md) | 是 | 真实累计用量 |

## 约束与提交

- 效果分类：`read`。
- 认证/上下文：`service`；范围及权限由服务端或Runner取得。
- 请求/动作ID去重与CAS按[统一规则](../CONVENTIONS.md)执行，重复ID不同参数必须冲突。
- 整合结果绑定全部输入依赖。
- 检查每项必需结果状态与实际版本
- 按输出契约读取证据/产物并区分候选与确认
- 冲突结论保留差异，必要查证后整合
- CAS提交共享板并回父Agent，缺口保留不伪造汇总成功
- 取消/超时遵从COMMON_CONTRACTS；所有引用必须当前权限内、版本可访问。

## 错误、等待、取消

- 必需子failed不能Join成功
- 旧结果返回stale
- 矛盾未解标partial

错误对象是 [Failure](../objects/Failure.md)；统一分类：schema_invalid / permission_denied / feature_disabled / revision_conflict / stale_resource / dependency_unavailable / budget_exceeded / deadline_exceeded / cancelled / unknown_effect。实际Runtime需要把业务错误映射到此对象；上述分类不会代替明确failed_phase和恢复提示。

只读可在有界策略内重试；写失败先核对动作账本，效果unknown时禁止盲重试；waiting通过审批决定、用户输入、process.poll或agents.wait推进。取消只停止后续执行，已有效果如实保留。

## 请求示例

示例展示结构；不代表这些示例引用存在。

```json
{
  "required_result_refs": [],
  "expected_task_revision": 0,
  "reducer_spec": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  }
}
```

## 成功结构示例

```json
{
  "kind": "ok",
  "payload": {
    "agent_ref": {
      "kind": "web",
      "id": "example_001",
      "version": "example_001"
    },
    "outcome": "succeeded",
    "summary": "example_001",
    "output_refs": [],
    "verification_refs": [],
    "limitations": [],
    "usage_ref": {
      "kind": "web",
      "id": "example_001",
      "version": "example_001"
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
| `agent.collaboration.join` | [开发设计](../../../docs/design/components/agent-collaboration-join.md) | `src/uaw/agent/collaboration/join.py` |

[接口机器目录](../../../contracts/interfaces.json) · [统一对象schema](../../../contracts/uaw.schema.json)
