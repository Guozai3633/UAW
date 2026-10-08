# tool.invocation.result

状态：契约0.1，待实现。类别：细分组件私有接口。所属：工具运行。

规范结果与结算的私有阶段输入。

[分类索引](../COMPONENT.md) · [统一规则](../CONVENTIONS.md) · [实际范围](../../implementation/README.md)

## 调用入口

计划Python异步签名：`async def handle(request: InternalToolInvocationResultRequest, context: TrustedExecutionContext) -> ComponentToolInvocationResultResult`。所属入口为 `tool.invocation.result`。该签名是契约目标；实际方法定位见对应开发设计，不能从公网/LLM直接调用私有组件。

## 输入

[InternalToolInvocationResultRequest](../objects/InternalToolInvocationResultRequest.md)；每个字段的类型、必填性、默认注解、限制和分支见对象页。

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `provider_result_ref` | [Ref](../objects/Ref.md) | 是 | 真实提供方响应原始记录，不含回显秘密。 |
| `effect_state` | [EffectState](../objects/EffectState.md) | 是 | 外部效果confirmed/pending/unknown，不能凭HTTP200推断。 |
| `attempt_usage` | [Usage](../objects/Usage.md) | 是 | 这次真实尝试的已知用量；未知账单标记pending。 |

## 输出

[ComponentToolInvocationResultResult](../objects/ComponentToolInvocationResultResult.md) 为完整返回结构。`kind=ok` 的payload是 [ToolResult](../objects/ToolResult.md)。`waiting`带wait_ref，其他非成功状态带Failure，不能用空对象假装成功。

| payload字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `call_ref` | [Ref](../objects/Ref.md) | 是 | 真实调用 |
| `status` | [ToolStatus](../objects/ToolStatus.md) | 是 | 成功/失败/等待/未知效果 |
| `data` | [Object](../objects/Object.md) | 否 | 由该工具output_schema约束的业务数据 |
| `output_refs` | 数组&lt;[Ref](../objects/Ref.md)&gt; | 是 | 大结果/文件/证据 |
| `failure` | [Failure](../objects/Failure.md) | 否 | 失败 |
| `effect_state` | [EffectState](../objects/EffectState.md) | 是 | 副作用确定性 |
| `usage_ref` | [Ref](../objects/Ref.md) | 是 | 调用用量 |
| `next_cursor` | [Cursor](../objects/Cursor.md) | 否 | 分页 |

## 约束与提交

- 效果分类：`read`。
- 认证/上下文：`service`；范围及权限由服务端或Runner取得。
- 请求/动作ID去重与CAS按[统一规则](../CONVENTIONS.md)执行，重复ID不同参数必须冲突。
- 结果提交和账本进展保持可恢复关联，终态仅由Run提交。
- 输出schema核验并分离业务与基础设施状态
- 确认或保留未决效果到账本
- 保存原始结果并分页/摘要
- 结算实际用量，向Run/Agent反馈类型结果
- 取消/超时遵从COMMON_CONTRACTS；所有引用必须当前权限内、版本可访问。

## 错误、等待、取消

- 缺业务状态不能猜成功
- 超大结果返回raw_ref与分页

错误对象是 [Failure](../objects/Failure.md)；统一分类：schema_invalid / permission_denied / feature_disabled / revision_conflict / stale_resource / dependency_unavailable / budget_exceeded / deadline_exceeded / cancelled / unknown_effect。实际Runtime需要把业务错误映射到此对象；上述分类不会代替明确failed_phase和恢复提示。

只读可在有界策略内重试；写失败先核对动作账本，效果unknown时禁止盲重试；waiting通过审批决定、用户输入、process.poll或agents.wait推进。取消只停止后续执行，已有效果如实保留。

## 请求示例

示例展示结构；不代表这些示例引用存在。

```json
{
  "provider_result_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "effect_state": "confirmed",
  "attempt_usage": {
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
}
```

## 成功结构示例

```json
{
  "kind": "ok",
  "payload": {
    "call_ref": {
      "kind": "web",
      "id": "example_001",
      "version": "example_001"
    },
    "status": "succeeded",
    "output_refs": [],
    "effect_state": "confirmed",
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
| `tool.invocation.result` | [开发设计](../../../docs/design/components/tool-invocation-result.md) | `src/uaw/tool/invocation/result.py` |

[接口机器目录](../../../contracts/interfaces.json) · [统一对象schema](../../../contracts/uaw.schema.json)
