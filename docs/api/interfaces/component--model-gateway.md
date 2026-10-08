# model.gateway

状态：契约0.1，待实现。类别：细分组件私有接口。所属：模型调用。

统一模型调用。

[分类索引](../COMPONENT.md) · [统一规则](../CONVENTIONS.md) · [实际范围](../../implementation/README.md)

## 调用入口

计划Python异步签名：`async def handle(request: ModelCall, context: TrustedExecutionContext) -> ComponentModelGatewayResult`。所属入口为 `model.gateway`。该签名是契约目标；实际方法定位见对应开发设计，不能从公网/LLM直接调用私有组件。

## 输入

[ModelCall](../objects/ModelCall.md)；每个字段的类型、必填性、默认注解、限制和分支见对象页。

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `context_snapshot_ref` | [Ref](../objects/Ref.md) | 是 | 快照 |
| `model_config` | [ResolvedModelConfig](../objects/ResolvedModelConfig.md) | 是 | 真实配置 |
| `output_protocol` | [Protocol](../objects/Protocol.md) | 是 | 结果协议 |
| `output_schema` | [Schema](../objects/Schema.md) | 否 | json_schema时必需 |
| `attempt_id` | [ID](../objects/ID.md) | 是 | 尝试 |

## 输出

[ComponentModelGatewayResult](../objects/ComponentModelGatewayResult.md) 为完整返回结构。`kind=ok` 的payload是 [ModelOutput](../objects/ModelOutput.md)。`waiting`带wait_ref，其他非成功状态带Failure，不能用空对象假装成功。

| payload字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `attempt_id` | [ID](../objects/ID.md) | 是 | 实际尝试 |
| `actual_config` | [ResolvedModelConfig](../objects/ResolvedModelConfig.md) | 是 | 真实配置 |
| `text` | [Text](../objects/Text.md) | 是 | 可见模型结果 |
| `tool_calls` | 数组&lt;[ToolCall](../objects/ToolCall.md)&gt; | 是 | 拟执行工具；尚未授权 |
| `structured_data` | [Object](../objects/Object.md) | 否 | 受output_schema约束的结果 |
| `finish_reason` | [FinishReason](../objects/FinishReason.md) | 是 | 正常/工具/截断等 |
| `usage` | [Usage](../objects/Usage.md) | 是 | 已知用量 |
| `content_ref` | [Ref](../objects/Ref.md) | 否 | 大输出的完整内容引用。 |
| `text_complete` | [Bool](../objects/Bool.md) | 是 | text是否包含本次收到的完整可见文本；不表示整个任务完成。 |

## 约束与提交

- 效果分类：`read`。
- 认证/上下文：`service`；范围及权限由服务端或Runner取得。
- 请求/动作ID去重与CAS按[统一规则](../CONVENTIONS.md)执行，重复ID不同参数必须冲突。
- 保存调用ID、模型/参数/输入引用与attempt，密钥不保存于prompt/log。
- 复核当前模型/提供方有效状态
- 向Run预留调用预算并服从剩余deadline
- 用服务端凭据选择adapter，规范请求
- 绑定流式attempt并验证动作输出
- 成功或失败都记录实际用量/费用，释放未用预留
- 类型化错误交Recovery
- 取消/超时遵从COMMON_CONTRACTS；所有引用必须当前权限内、版本可访问。

## 错误、等待、取消

- 配额不足不发送
- 协议不支持明确unsupported
- 传输取消不假装供应商未计费

错误对象是 [Failure](../objects/Failure.md)；统一分类：schema_invalid / permission_denied / feature_disabled / revision_conflict / stale_resource / dependency_unavailable / budget_exceeded / deadline_exceeded / cancelled / unknown_effect。实际Runtime需要把业务错误映射到此对象；上述分类不会代替明确failed_phase和恢复提示。

只读可在有界策略内重试；写失败先核对动作账本，效果unknown时禁止盲重试；waiting通过审批决定、用户输入、process.poll或agents.wait推进。取消只停止后续执行，已有效果如实保留。

## 请求示例

示例展示结构；不代表这些示例引用存在。

```json
{
  "context_snapshot_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "model_config": {
    "model_id": "example_001",
    "catalog_revision": 0,
    "provider_ref": {
      "kind": "web",
      "id": "example_001",
      "version": "example_001"
    },
    "policy_ref": {
      "kind": "web",
      "id": "example_001",
      "version": "example_001"
    },
    "max_output_tokens": 0
  },
  "output_protocol": "text",
  "attempt_id": "example_001"
}
```

## 成功结构示例

```json
{
  "kind": "ok",
  "payload": {
    "attempt_id": "example_001",
    "actual_config": {
      "model_id": "example_001",
      "catalog_revision": 0,
      "provider_ref": {
        "kind": "web",
        "id": "example_001",
        "version": "example_001"
      },
      "policy_ref": {
        "kind": "web",
        "id": "example_001",
        "version": "example_001"
      },
      "max_output_tokens": 0
    },
    "text": "example_001",
    "tool_calls": [],
    "finish_reason": "stop",
    "usage": {
      "attempt_id": "example_001",
      "resources": {
        "currency": "CNY",
        "input_tokens": 0,
        "output_tokens": 0,
        "model_calls": 0,
        "tool_calls": 0,
        "child_agents": 0,
        "wall_time_ms": 0,
        "money": "0"
      },
      "billing_state": "confirmed"
    },
    "text_complete": true
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
| `model.gateway` | [开发设计](../../../docs/design/components/model-gateway.md) | `src/uaw/model/gateway.py` |

[接口机器目录](../../../contracts/interfaces.json) · [统一对象schema](../../../contracts/uaw.schema.json)
