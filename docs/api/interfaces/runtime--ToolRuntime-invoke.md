# ToolRuntime.invoke

状态：契约0.1，待实现。类别：Runtime 公共入口。所属：工具运行。

模型只能提出工具名、参数和动作去重键。

[分类索引](../RUNTIME.md) · [统一规则](../CONVENTIONS.md) · [实际范围](../../implementation/README.md)

## 调用入口

计划Python异步签名：`async def invoke(request: ToolCall, context: TrustedExecutionContext) -> RuntimeToolruntimeInvokeResult`。所属入口为 `ToolRuntime.invoke`。该签名是契约目标；实际方法定位见对应开发设计，不能从公网/LLM直接调用私有组件。

## 输入

[ToolCall](../objects/ToolCall.md)；每个字段的类型、必填性、默认注解、限制和分支见对象页。

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `tool_ref` | [Ref](../objects/Ref.md) | 是 | 固定工具版本 |
| `arguments` | [Object](../objects/Object.md) | 是 | 依据input_schema再次校验 |
| `action_id` | [ID](../objects/ID.md) | 是 | 跨重试保持不变的逻辑动作 |

## 输出

[RuntimeToolruntimeInvokeResult](../objects/RuntimeToolruntimeInvokeResult.md) 为完整返回结构。`kind=ok` 的payload是 [ToolResult](../objects/ToolResult.md)。`waiting`带wait_ref，其他非成功状态带Failure，不能用空对象假装成功。

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

- 效果分类：`external_write`。
- 认证/上下文：`service`；范围及权限由服务端或Runner取得。
- 请求/动作ID去重与CAS按[统一规则](../CONVENTIONS.md)执行，重复ID不同参数必须冲突。
- effect由固定ToolSpec确定，不由调用者指定；本描述是最大风险上限。

## 错误、等待、取消

错误对象是 [Failure](../objects/Failure.md)；统一分类：schema_invalid / permission_denied / feature_disabled / revision_conflict / stale_resource / dependency_unavailable / budget_exceeded / deadline_exceeded / cancelled / unknown_effect。实际Runtime需要把业务错误映射到此对象；上述分类不会代替明确failed_phase和恢复提示。

只读可在有界策略内重试；写失败先核对动作账本，效果unknown时禁止盲重试；waiting通过审批决定、用户输入、process.poll或agents.wait推进。取消只停止后续执行，已有效果如实保留。

## 请求示例

示例展示结构；不代表这些示例引用存在。

```json
{
  "tool_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "arguments": {},
  "action_id": "example_001"
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
| `tool` | [开发设计](../../../docs/design/modules/tool.md) | `src/uaw/tool/facade.py` |
| `tool.invocation` | [开发设计](../../../docs/design/components/tool-invocation.md) | `src/uaw/tool/invocation/facade.py` |

[接口机器目录](../../../contracts/interfaces.json) · [统一对象schema](../../../contracts/uaw.schema.json)
