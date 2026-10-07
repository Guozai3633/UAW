# agent.collaboration.channel

状态：契约0.1，待实现。类别：细分组件私有接口。所属：Agent执行与协作。

消息与受控引用的私有阶段输入。

[分类索引](../COMPONENT.md) · [统一规则](../CONVENTIONS.md) · [实际范围](../../implementation/README.md)

## 调用入口

计划Python异步签名：`async def handle(request: InternalAgentCollaborationChannelRequest, context: TrustedExecutionContext) -> ComponentAgentCollaborationChannelResult`。所属入口为 `agent.collaboration.channel`。该签名是契约目标；实际方法定位见对应开发设计，不能从公网/LLM直接调用私有组件。

## 输入

[InternalAgentCollaborationChannelRequest](../objects/InternalAgentCollaborationChannelRequest.md)；每个字段的类型、必填性、默认注解、限制和分支见对象页。

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `message_id` | [ID](../objects/ID.md) | 是 | 协作消息去重键，重复同内容返回原消息。 |
| `from_ref` | [Ref](../objects/Ref.md) | 是 | 同任务树内真实发送者，由认证上下文核验。 |
| `to_ref` | [Ref](../objects/Ref.md) | 是 | 同任务树获准接收实例，不能越界投递资料。 |
| `payload_refs` | 数组&lt;[Ref](../objects/Ref.md)&gt; | 是 | 允许共享的固定资料/候选结果，不传整个私有上下文。 |
| `task_revision` | [Revision](../objects/Revision.md) | 是 | 协作消息或结果依赖的共同任务修订。 |

## 输出

[ComponentAgentCollaborationChannelResult](../objects/ComponentAgentCollaborationChannelResult.md) 为完整返回结构。`kind=ok` 的payload是 [AgentMessage](../objects/AgentMessage.md)。`waiting`带wait_ref，其他非成功状态带Failure，不能用空对象假装成功。

| payload字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `message_id` | [ID](../objects/ID.md) | 是 | 通道去重键 |
| `from_ref` | [Ref](../objects/Ref.md) | 是 | 发送实例 |
| `to_ref` | [Ref](../objects/Ref.md) | 是 | 接收实例 |
| `task_revision` | [Revision](../objects/Revision.md) | 是 | 共同任务基线 |
| `text` | [Text](../objects/Text.md) | 是 | 协作内容 |
| `payload_refs` | 数组&lt;[Ref](../objects/Ref.md)&gt; | 是 | 共享资料/候选结果 |
| `created_at` | [Timestamp](../objects/Timestamp.md) | 是 | 提交时间 |

## 约束与提交

- 效果分类：`read`。
- 认证/上下文：`service`；范围及权限由服务端或Runner取得。
- 请求/动作ID去重与CAS按[统一规则](../CONVENTIONS.md)执行，重复ID不同参数必须冲突。
- 消息记录归Agent，Run事件仅引用；不共享完整prompt。
- 核对同任务关系和收发权限
- 消息注明目标/引用/期待回复/deadline
- 关键分配/结果消息持久去重，临时进度按策略保留
- 接收者按自己scope重新解析引用，控制互聊深度与次数
- 取消/超时遵从COMMON_CONTRACTS；所有引用必须当前权限内、版本可访问。

## 错误、等待、取消

- 过期目标返回stale_message
- 无权引用不送达正文

错误对象是 [Failure](../objects/Failure.md)；统一分类：schema_invalid / permission_denied / feature_disabled / revision_conflict / stale_resource / dependency_unavailable / budget_exceeded / deadline_exceeded / cancelled / unknown_effect。实际Runtime需要把业务错误映射到此对象；上述分类不会代替明确failed_phase和恢复提示。

只读可在有界策略内重试；写失败先核对动作账本，效果unknown时禁止盲重试；waiting通过审批决定、用户输入、process.poll或agents.wait推进。取消只停止后续执行，已有效果如实保留。

## 请求示例

示例展示结构；不代表这些示例引用存在。

```json
{
  "message_id": "example_001",
  "from_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "to_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "payload_refs": [],
  "task_revision": 0
}
```

## 成功结构示例

```json
{
  "kind": "ok",
  "payload": {
    "message_id": "example_001",
    "from_ref": {
      "kind": "web",
      "id": "example_001",
      "version": "example_001"
    },
    "to_ref": {
      "kind": "web",
      "id": "example_001",
      "version": "example_001"
    },
    "task_revision": 0,
    "text": "example_001",
    "payload_refs": [],
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
| `agent.collaboration.channel` | [开发设计](../../../docs/design/components/agent-collaboration-channel.md) | `src/uaw/agent/collaboration/channel.py` |

[接口机器目录](../../../contracts/interfaces.json) · [统一对象schema](../../../contracts/uaw.schema.json)
