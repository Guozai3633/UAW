# agent.definitions.discovery

状态：契约0.1，待实现。类别：细分组件私有接口。所属：Agent执行与协作。

会话Agent发现的私有阶段输入。

[分类索引](../COMPONENT.md) · [统一规则](../CONVENTIONS.md) · [实际范围](../../implementation/README.md)

## 调用入口

计划Python异步签名：`async def handle(request: InternalAgentDefinitionsDiscoveryRequest, context: TrustedExecutionContext) -> ComponentAgentDefinitionsDiscoveryResult`。所属入口为 `agent.definitions.discovery`。该签名是契约目标；实际方法定位见对应开发设计，不能从公网/LLM直接调用私有组件。

## 输入

[InternalAgentDefinitionsDiscoveryRequest](../objects/InternalAgentDefinitionsDiscoveryRequest.md)；每个字段的类型、必填性、默认注解、限制和分支见对象页。

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `conversation_id` | [ID](../objects/ID.md) | 是 | 当前获准会话，服务校验与可信上下文一致。 |
| `task_goal` | [Text](../objects/Text.md) | 是 | 当前目标摘要，仅用于候选排序，不覆盖原文。 |
| `role_constraints` | 数组&lt;[Text](../objects/Text.md)&gt; | 是 | 任务所需职责与不能进行的动作。 |
| `max_candidates` | integer | 是 | 一次最多提供候选数，减少模型输入而不授予权限。 |
| `definitions_revision` | [Revision](../objects/Revision.md) | 是 | 候选角色目录修订，用于缓存及失效。 |

## 输出

[ComponentAgentDefinitionsDiscoveryResult](../objects/ComponentAgentDefinitionsDiscoveryResult.md) 为完整返回结构。`kind=ok` 的payload是 [CandidatePage](../objects/CandidatePage.md)。`waiting`带wait_ref，其他非成功状态带Failure，不能用空对象假装成功。

| payload字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `items` | 数组&lt;[AgentCandidate](../objects/AgentCandidate.md)&gt; | 是 | 本页 |
| `next_cursor` | [Cursor](../objects/Cursor.md) | 否 | 续页 |
| `snapshot_revision` | [Revision](../objects/Revision.md) | 是 | 读取版本 |

## 约束与提交

- 效果分类：`read`。
- 认证/上下文：`service`；范围及权限由服务端或Runner取得。
- 请求/动作ID去重与CAS按[统一规则](../CONVENTIONS.md)执行，重复ID不同参数必须冲突。
- 候选仅诊断/缓存派生；发现不创建实例、不批权限。
- 按owner/conversation、enabled、flag/权限与能力过滤
- 小集合直接提供摘要，大集合关键词/向量召回
- 比对职责、use_when/avoid_when、输入输出与资源状态
- 返回带版本候选给当前LLM决定自己做/委派
- 选中后加载长方法，invoke再次复核
- 取消/超时遵从COMMON_CONTRACTS；所有引用必须当前权限内、版本可访问。

## 错误、等待、取消

- 无候选返回agent_capability_gap
- 停用/旧索引候选丢弃
- 跨会话未经授权拒绝

错误对象是 [Failure](../objects/Failure.md)；统一分类：schema_invalid / permission_denied / feature_disabled / revision_conflict / stale_resource / dependency_unavailable / budget_exceeded / deadline_exceeded / cancelled / unknown_effect。实际Runtime需要把业务错误映射到此对象；上述分类不会代替明确failed_phase和恢复提示。

只读可在有界策略内重试；写失败先核对动作账本，效果unknown时禁止盲重试；waiting通过审批决定、用户输入、process.poll或agents.wait推进。取消只停止后续执行，已有效果如实保留。

## 请求示例

示例展示结构；不代表这些示例引用存在。

```json
{
  "conversation_id": "example_001",
  "task_goal": "example_001",
  "role_constraints": [],
  "max_candidates": 1,
  "definitions_revision": 0
}
```

## 成功结构示例

```json
{
  "kind": "ok",
  "payload": {
    "items": [],
    "snapshot_revision": 0
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
| `agent.definitions.discovery` | [开发设计](../../../docs/design/components/agent-definitions-discovery.md) | `src/uaw/agent/definitions/discovery.py` |

[接口机器目录](../../../contracts/interfaces.json) · [统一对象schema](../../../contracts/uaw.schema.json)
