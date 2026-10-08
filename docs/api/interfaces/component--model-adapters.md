# model.adapters

状态：契约0.1，待实现。类别：细分组件私有接口。所属：模型调用。

供应商协议适配的私有阶段输入。

[分类索引](../COMPONENT.md) · [统一规则](../CONVENTIONS.md) · [实际范围](../../implementation/README.md)

## 调用入口

计划Python异步签名：`async def handle(request: InternalModelAdaptersRequest, context: TrustedExecutionContext) -> ComponentModelAdaptersResult`。所属入口为 `model.adapters`。该签名是契约目标；实际方法定位见对应开发设计，不能从公网/LLM直接调用私有组件。

## 输入

[InternalModelAdaptersRequest](../objects/InternalModelAdaptersRequest.md)；每个字段的类型、必填性、默认注解、限制和分支见对象页。

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `provider_ref` | [Ref](../objects/Ref.md) | 是 | 管理员配置且当前可用的固定提供方版本。 |
| `resolved_model_id` | [ID](../objects/ID.md) | 是 | 在用户固定政策或Auto授权内解析的实际目录ID。 |
| `messages` | 数组&lt;[Message](../objects/Message.md)&gt; | 是 | 按顺序发送给提供方的有来源消息块。 |
| `tools` | 数组&lt;[Schema](../objects/Schema.md)&gt; | 是 | 本次实际暴露给模型的工具参数schema，按稳定版本排序。 |
| `reasoning_config` | [ReasoningConfiguration](../objects/ReasoningConfiguration.md) | 否 | 支持的推理配置，不接受任意Object或用户模型替换。 |

## 输出

[ComponentModelAdaptersResult](../objects/ComponentModelAdaptersResult.md) 为完整返回结构。`kind=ok` 的payload是 [ProviderReceipt](../objects/ProviderReceipt.md)。`waiting`带wait_ref，其他非成功状态带Failure，不能用空对象假装成功。

| payload字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `attempt_id` | [ID](../objects/ID.md) | 是 | 实际尝试 |
| `raw_result_ref` | [Ref](../objects/Ref.md) | 是 | 原始响应 |
| `transport_status` | [NonEmptyText](../objects/NonEmptyText.md) | 是 | 传输状态 |
| `effect_state` | [EffectState](../objects/EffectState.md) | 是 | 效果确定性 |
| `usage` | [Usage](../objects/Usage.md) | 是 | 实际用量 |

## 约束与提交

- 效果分类：`read`。
- 认证/上下文：`service`；范围及权限由服务端或Runner取得。
- 请求/动作ID去重与CAS按[统一规则](../CONVENTIONS.md)执行，重复ID不同参数必须冲突。
- adapter协议版本固定，供应商响应标识用于对账；不伪造统一能力。
- 按adapter能力声明转消息/工具schema
- 检查具体模型支持的推理/结构参数
- 解析流式增量、工具参数与最终usage
- 保留供应商实际model/version和缓存用量
- 规范错误码但同时保留可诊断原始受控引用
- 取消/超时遵从COMMON_CONTRACTS；所有引用必须当前权限内、版本可访问。

## 错误、等待、取消

- 字段不支持返回unsupported
- 流截断标incomplete
- usage缺失标pending_usage不估成零

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
  "resolved_model_id": "example_001",
  "messages": [],
  "tools": []
}
```

## 成功结构示例

```json
{
  "kind": "ok",
  "payload": {
    "attempt_id": "example_001",
    "raw_result_ref": {
      "kind": "web",
      "id": "example_001",
      "version": "example_001"
    },
    "transport_status": "example_001",
    "effect_state": "confirmed",
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
| `model.adapters` | [开发设计](../../../docs/design/components/model-adapters.md) | `src/uaw/model/adapters.py` |

[接口机器目录](../../../contracts/interfaces.json) · [统一对象schema](../../../contracts/uaw.schema.json)
