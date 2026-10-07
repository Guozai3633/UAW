# AgentRuntime.start

状态：契约0.1，待实现。类别：Runtime 公共入口。所属：Agent执行与协作。

创建根执行实例。

[分类索引](../RUNTIME.md) · [统一规则](../CONVENTIONS.md) · [实际范围](../../implementation/README.md)

## 调用入口

计划Python异步签名：`async def start(request: AgentStartRequest, context: TrustedExecutionContext) -> RuntimeAgentruntimeStartResult`。所属入口为 `AgentRuntime.start`。该签名是契约目标；实际方法定位见对应开发设计，不能从公网/LLM直接调用私有组件。

## 输入

[AgentStartRequest](../objects/AgentStartRequest.md)；每个字段的类型、必填性、默认注解、限制和分支见对象页。

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `run_ref` | [Ref](../objects/Ref.md) | 是 | 当前运行 |
| `task_frame_ref` | [Ref](../objects/Ref.md) | 是 | 理解 |
| `creation_key` | [ID](../objects/ID.md) | 是 | 去重键 |
| `role_profile_ref` | [Ref](../objects/Ref.md) | 否 | 默认角色 |

## 输出

[RuntimeAgentruntimeStartResult](../objects/RuntimeAgentruntimeStartResult.md) 为完整返回结构。`kind=ok` 的payload是 [AgentInstance](../objects/AgentInstance.md)。`waiting`带wait_ref，其他非成功状态带Failure，不能用空对象假装成功。

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


## 错误、等待、取消

错误对象是 [Failure](../objects/Failure.md)；统一分类：schema_invalid / permission_denied / feature_disabled / revision_conflict / stale_resource / dependency_unavailable / budget_exceeded / deadline_exceeded / cancelled / unknown_effect。实际Runtime需要把业务错误映射到此对象；上述分类不会代替明确failed_phase和恢复提示。

只读可在有界策略内重试；写失败先核对动作账本，效果unknown时禁止盲重试；waiting通过审批决定、用户输入、process.poll或agents.wait推进。取消只停止后续执行，已有效果如实保留。

## 请求示例

示例展示结构；不代表这些示例引用存在。

```json
{
  "run_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "task_frame_ref": {
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
| `agent` | [开发设计](../../../docs/design/modules/agent.md) | `src/uaw/agent/facade.py` |
| `agent.factory` | [开发设计](../../../docs/design/components/agent-factory.md) | `src/uaw/agent/factory.py` |

[接口机器目录](../../../contracts/interfaces.json) · [统一对象schema](../../../contracts/uaw.schema.json)
