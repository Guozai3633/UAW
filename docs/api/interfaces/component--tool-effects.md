# tool.effects

状态：契约0.1，待实现。类别：细分组件私有接口。所属：工具运行。

互斥分支；所有字段须匹配所选action。

[分类索引](../COMPONENT.md) · [统一规则](../CONVENTIONS.md) · [实际范围](../../implementation/README.md)

## 调用入口

计划Python异步签名：`async def handle(request: InternalToolEffectsRequest, context: TrustedExecutionContext) -> ComponentToolEffectsResult`。所属入口为 `tool.effects`。该签名是契约目标；实际方法定位见对应开发设计，不能从公网/LLM直接调用私有组件。

## 输入

[InternalToolEffectsRequest](../objects/InternalToolEffectsRequest.md)；每个字段的类型、必填性、默认注解、限制和分支见对象页。

动作分支：

- [InternalToolEffectsRequestRecordIntent](../objects/InternalToolEffectsRequestRecordIntent.md)
- [InternalToolEffectsRequestReconcile](../objects/InternalToolEffectsRequestReconcile.md)

## 输出

[ComponentToolEffectsResult](../objects/ComponentToolEffectsResult.md) 为完整返回结构。`kind=ok` 的payload是 [InternalToolEffectsOutput](../objects/InternalToolEffectsOutput.md)。`waiting`带wait_ref，其他非成功状态带Failure，不能用空对象假装成功。


## 约束与提交

- 效果分类：`read`。
- 认证/上下文：`service`；范围及权限由服务端或Runner取得。
- 请求/动作ID去重与CAS按[统一规则](../CONVENTIONS.md)执行，重复ID不同参数必须冲突。
- 动作与attempt分开，重试不换逻辑action/business key；外部幂等仍需提供方支持。
- 执行前持久保存pending意图与稳定业务键
- 适配器发送并保存真实请求/回应引用
- confirmed仅在提供方状态足够明确时记录
- 网络中断/崩溃结果未知标unknown
- 恢复用业务键/请求ID查询实际状态
- 确定未发生且契约允许后才能重试
- 取消/超时遵从COMMON_CONTRACTS；所有引用必须当前权限内、版本可访问。

## 错误、等待、取消

- 无法查询保持unknown且阻止依赖成功
- 重复回执幂等提交
- 提供方不支持对账需用户/人工处理

错误对象是 [Failure](../objects/Failure.md)；统一分类：schema_invalid / permission_denied / feature_disabled / revision_conflict / stale_resource / dependency_unavailable / budget_exceeded / deadline_exceeded / cancelled / unknown_effect。实际Runtime需要把业务错误映射到此对象；上述分类不会代替明确failed_phase和恢复提示。

只读可在有界策略内重试；写失败先核对动作账本，效果unknown时禁止盲重试；waiting通过审批决定、用户输入、process.poll或agents.wait推进。取消只停止后续执行，已有效果如实保留。

## 请求示例

示例展示结构；不代表这些示例引用存在。

```json
{
  "action": "record_intent",
  "parameters": {
    "action_id": "example_001",
    "normalized_arguments_hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
    "provider_ref": {
      "kind": "web",
      "id": "example_001",
      "version": "example_001"
    },
    "attempt_id": "example_001"
  }
}
```

## 成功结构示例

```json
{
  "kind": "ok",
  "payload": {
    "action": "record_intent",
    "result": {
      "action_id": "example_001",
      "arguments_hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "provider_ref": {
        "kind": "web",
        "id": "example_001",
        "version": "example_001"
      },
      "attempt_ids": [],
      "state": "confirmed",
      "revision": 0
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
| `tool.effects` | [开发设计](../../../docs/design/components/tool-effects.md) | `src/uaw/tool/effects.py` |

[接口机器目录](../../../contracts/interfaces.json) · [统一对象schema](../../../contracts/uaw.schema.json)
