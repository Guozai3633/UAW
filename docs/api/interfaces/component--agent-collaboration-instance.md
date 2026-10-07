# agent.collaboration.instance

状态：契约0.1，待实现。类别：细分组件私有接口。所属：Agent执行与协作。

隔离运行实例的私有阶段输入。

[分类索引](../COMPONENT.md) · [统一规则](../CONVENTIONS.md) · [实际范围](../../implementation/README.md)

## 调用入口

计划Python异步签名：`async def handle(request: InternalAgentCollaborationInstanceRequest, context: TrustedExecutionContext) -> ComponentAgentCollaborationInstanceResult`。所属入口为 `agent.collaboration.instance`。该签名是契约目标；实际方法定位见对应开发设计，不能从公网/LLM直接调用私有组件。

## 输入

[InternalAgentCollaborationInstanceRequest](../objects/InternalAgentCollaborationInstanceRequest.md)；每个字段的类型、必填性、默认注解、限制和分支见对象页。

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `definition_ref` | [Ref](../objects/Ref.md) | 是 | 可用且绑定当前会话的固定角色定义版本。 |
| `delegation_ref` | [Ref](../objects/Ref.md) | 是 | 目标、资料、验收与预算已经固定的委派契约。 |
| `parent_agent_ref` | [Ref](../objects/Ref.md) | 是 | 父实例必须同一任务树且仍拥有有效权限/预算。 |
| `creation_key` | [Text](../objects/Text.md) | 是 | 重复创建同一输入返回已有实例；不同输入相同键冲突。 |

## 输出

[ComponentAgentCollaborationInstanceResult](../objects/ComponentAgentCollaborationInstanceResult.md) 为完整返回结构。`kind=ok` 的payload是 [AgentInstance](../objects/AgentInstance.md)。`waiting`带wait_ref，其他非成功状态带Failure，不能用空对象假装成功。

| payload字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `id` | [ID](../objects/ID.md) | 是 | 实例ID |
| `run_id` | [ID](../objects/ID.md) | 是 | 所属运行 |
| `parent_agent_ref` | [Ref](../objects/Ref.md) | 否 | 根实例无父 |
| `definition_ref` | [Ref](../objects/Ref.md) | 否 | 使用的角色版本 |
| `delegation_ref` | [Ref](../objects/Ref.md) | 否 | 子实例的委派契约 |
| `status` | [State](../objects/State.md) | 是 | 实例状态 |
| `model_policy_ref` | [Ref](../objects/Ref.md) | 是 | 实际继承或覆盖政策 |
| `capability_policy_ref` | [Ref](../objects/Ref.md) | 是 | 有效权限交集 |
| `context_epoch` | [Revision](../objects/Revision.md) | 是 | 上下文纪元 |
| `workspace_ref` | [Ref](../objects/Ref.md) | 否 | 需要文件操作时绑定 |
| `result_ref` | [Ref](../objects/Ref.md) | 否 | 终态结果 |
| `revision` | [Revision](../objects/Revision.md) | 是 | 实例版本 |

## 约束与提交

- 效果分类：`internal_write`。
- 认证/上下文：`service`；范围及权限由服务端或Runner取得。
- 请求/动作ID去重与CAS按[统一规则](../CONVENTIONS.md)执行，重复ID不同参数必须冲突。
- 实例状态与定义分开，复用定义不复用scratch。
- 工厂校验定义enabled及精确版本
- 解析继承模型与角色权限交集
- 预留子预算并分配私有上下文，写任务需要隔离工作区
- 持久实例关联后调度，反馈丢失按creation_key查询
- 取消/超时遵从COMMON_CONTRACTS；所有引用必须当前权限内、版本可访问。

## 错误、等待、取消

- 定义停用拒绝新实例
- 模型无效返回主LLM
- 预留失败回收分配意图

错误对象是 [Failure](../objects/Failure.md)；统一分类：schema_invalid / permission_denied / feature_disabled / revision_conflict / stale_resource / dependency_unavailable / budget_exceeded / deadline_exceeded / cancelled / unknown_effect。实际Runtime需要把业务错误映射到此对象；上述分类不会代替明确failed_phase和恢复提示。

只读可在有界策略内重试；写失败先核对动作账本，效果unknown时禁止盲重试；waiting通过审批决定、用户输入、process.poll或agents.wait推进。取消只停止后续执行，已有效果如实保留。

## 请求示例

示例展示结构；不代表这些示例引用存在。

```json
{
  "definition_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "delegation_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "parent_agent_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "creation_key": "example_001"
}
```

## 成功结构示例

```json
{
  "kind": "ok",
  "payload": {
    "id": "example_001",
    "run_id": "example_001",
    "status": "pending",
    "model_policy_ref": {
      "kind": "web",
      "id": "example_001",
      "version": "example_001"
    },
    "capability_policy_ref": {
      "kind": "web",
      "id": "example_001",
      "version": "example_001"
    },
    "context_epoch": 0,
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
| `agent.collaboration.instance` | [开发设计](../../../docs/design/components/agent-collaboration-instance.md) | `src/uaw/agent/collaboration/instance.py` |

[接口机器目录](../../../contracts/interfaces.json) · [统一对象schema](../../../contracts/uaw.schema.json)
