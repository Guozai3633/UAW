# model.usage

状态：契约0.1，待实现。类别：细分组件私有接口。所属：模型调用。

计量与版本记录的私有阶段输入。

[分类索引](../COMPONENT.md) · [统一规则](../CONVENTIONS.md) · [实际范围](../../implementation/README.md)

## 调用入口

计划Python异步签名：`async def handle(request: InternalModelUsageRequest, context: TrustedExecutionContext) -> ComponentModelUsageResult`。所属入口为 `model.usage`。该签名是契约目标；实际方法定位见对应开发设计，不能从公网/LLM直接调用私有组件。

## 输入

[InternalModelUsageRequest](../objects/InternalModelUsageRequest.md)；每个字段的类型、必填性、默认注解、限制和分支见对象页。

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `call_ref` | [Ref](../objects/Ref.md) | 是 | 实际调用记录及固定参数版本。 |
| `provider_usage` | [Usage](../objects/Usage.md) | 否 | 提供方报告的实际账单；无数据则pending而非0。 |
| `reserved_budget_ref` | [Ref](../objects/Ref.md) | 是 | 本次模型调用对应预算预留。 |
| `actual_config_ref` | [Ref](../objects/Ref.md) | 是 | 本次真实使用的模型配置，不能只记录用户希望的配置。 |

## 输出

[ComponentModelUsageResult](../objects/ComponentModelUsageResult.md) 为完整返回结构。`kind=ok` 的payload是 [UsageSettlement](../objects/UsageSettlement.md)。`waiting`带wait_ref，其他非成功状态带Failure，不能用空对象假装成功。

| payload字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `reservation_ref` | [Ref](../objects/Ref.md) | 是 | 预留 |
| `usage_refs` | 数组&lt;[Ref](../objects/Ref.md)&gt; | 是 | 所有attempt |
| `remaining` | [ResourceVector](../objects/ResourceVector.md) | 是 | 剩余 |
| `revision` | [Revision](../objects/Revision.md) | 是 | 账本版本 |
| `billing_pending` | [Bool](../objects/Bool.md) | 是 | 是否待账单 |

## 约束与提交

- 效果分类：`read`。
- 认证/上下文：`service`；范围及权限由服务端或Runner取得。
- 请求/动作ID去重与CAS按[统一规则](../CONVENTIONS.md)执行，重复ID不同参数必须冲突。
- Model拥有调用记录，Run Budget Ledger是预算余额权威；重复回执不能二次扣账。
- 核对attempt和供应商响应标识去重usage
- 区分输入/输出/推理/缓存字段的实际计费口径
- 结算预留与实际费用，未知费用留待核对
- 回传预算警告与诊断指标
- 记录实际模型版本而非用户显示名称
- 取消/超时遵从COMMON_CONTRACTS；所有引用必须当前权限内、版本可访问。

## 错误、等待、取消

- usage缺失返回pending
- 超出预留立即限制后续动作并报告
- 金额口径未知不伪造价格

错误对象是 [Failure](../objects/Failure.md)；统一分类：schema_invalid / permission_denied / feature_disabled / revision_conflict / stale_resource / dependency_unavailable / budget_exceeded / deadline_exceeded / cancelled / unknown_effect。实际Runtime需要把业务错误映射到此对象；上述分类不会代替明确failed_phase和恢复提示。

只读可在有界策略内重试；写失败先核对动作账本，效果unknown时禁止盲重试；waiting通过审批决定、用户输入、process.poll或agents.wait推进。取消只停止后续执行，已有效果如实保留。

## 请求示例

示例展示结构；不代表这些示例引用存在。

```json
{
  "call_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "reserved_budget_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "actual_config_ref": {
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
    "reservation_ref": {
      "kind": "web",
      "id": "example_001",
      "version": "example_001"
    },
    "usage_refs": [],
    "remaining": {
      "input_tokens": 0,
      "output_tokens": 0,
      "model_calls": 0,
      "tool_calls": 0,
      "child_agents": 0,
      "wall_time_ms": 0,
      "money": "0",
      "currency": "CNY"
    },
    "revision": 0,
    "billing_pending": true
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
| `model.usage` | [开发设计](../../../docs/design/components/model-usage.md) | `src/uaw/model/usage.py` |

[接口机器目录](../../../contracts/interfaces.json) · [统一对象schema](../../../contracts/uaw.schema.json)
