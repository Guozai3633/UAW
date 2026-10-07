# tool.invocation.precheck

状态：契约0.1，待实现。类别：细分组件私有接口。所属：工具运行。

执行预检的私有阶段输入。

[分类索引](../COMPONENT.md) · [统一规则](../CONVENTIONS.md) · [实际范围](../../implementation/README.md)

## 调用入口

计划Python异步签名：`async def handle(request: InternalToolInvocationPrecheckRequest, context: TrustedExecutionContext) -> ComponentToolInvocationPrecheckResult`。所属入口为 `tool.invocation.precheck`。该签名是契约目标；实际方法定位见对应开发设计，不能从公网/LLM直接调用私有组件。

## 输入

[InternalToolInvocationPrecheckRequest](../objects/InternalToolInvocationPrecheckRequest.md)；每个字段的类型、必填性、默认注解、限制和分支见对象页。

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `validated_call_ref` | [Ref](../objects/Ref.md) | 是 | 已规范化、已授权调用记录及版本。 |
| `effective_policy_ref` | [Ref](../objects/Ref.md) | 是 | 当前有效权限/旗标/审批政策版本。 |
| `budget_estimate` | [ResourceVector](../objects/ResourceVector.md) | 是 | 派发前估算的资源，失败尝试也进入结算。 |

## 输出

[ComponentToolInvocationPrecheckResult](../objects/ComponentToolInvocationPrecheckResult.md) 为完整返回结构。`kind=ok` 的payload是 [PrecheckDecision](../objects/PrecheckDecision.md)。`waiting`带wait_ref，其他非成功状态带Failure，不能用空对象假装成功。

| payload字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `allowed` | [Bool](../objects/Bool.md) | 是 | 可否继续 |
| `approval_required` | [Bool](../objects/Bool.md) | 是 | 是否审批 |
| `policy_ref` | [Ref](../objects/Ref.md) | 是 | 有效政策 |
| `resource_refs` | 数组&lt;[Ref](../objects/Ref.md)&gt; | 是 | 实际基线 |
| `reservation_ref` | [Ref](../objects/Ref.md) | 否 | 已预留资源 |
| `violations` | 数组&lt;[ValidationIssue](../objects/ValidationIssue.md)&gt; | 是 | 阻碍 |

## 约束与提交

- 效果分类：`read`。
- 认证/上下文：`service`；范围及权限由服务端或Runner取得。
- 请求/动作ID去重与CAS按[统一规则](../CONVENTIONS.md)执行，重复ID不同参数必须冲突。
- PrecheckDecision短时记录不是永久授权。
- 按当前主体/资源检查flag与能力
- 按实际副作用类别判断风险，不看工具名字猜只读
- 检查剩余deadline和预算
- 返回允许/需审批/拒绝，尚不执行
- 取消/超时遵从COMMON_CONTRACTS；所有引用必须当前权限内、版本可访问。

## 错误、等待、取消

- policy_denied不能替换工具绕过
- budget_exceeded返回资源缺口

错误对象是 [Failure](../objects/Failure.md)；统一分类：schema_invalid / permission_denied / feature_disabled / revision_conflict / stale_resource / dependency_unavailable / budget_exceeded / deadline_exceeded / cancelled / unknown_effect。实际Runtime需要把业务错误映射到此对象；上述分类不会代替明确failed_phase和恢复提示。

只读可在有界策略内重试；写失败先核对动作账本，效果unknown时禁止盲重试；waiting通过审批决定、用户输入、process.poll或agents.wait推进。取消只停止后续执行，已有效果如实保留。

## 请求示例

示例展示结构；不代表这些示例引用存在。

```json
{
  "validated_call_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "effective_policy_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "budget_estimate": {
    "input_tokens": 0,
    "output_tokens": 0,
    "model_calls": 0,
    "tool_calls": 0,
    "child_agents": 0,
    "wall_time_ms": 0,
    "money": "0",
    "currency": "CNY"
  }
}
```

## 成功结构示例

```json
{
  "kind": "ok",
  "payload": {
    "allowed": true,
    "approval_required": true,
    "policy_ref": {
      "kind": "web",
      "id": "example_001",
      "version": "example_001"
    },
    "resource_refs": [],
    "violations": []
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
| `tool.invocation.precheck` | [开发设计](../../../docs/design/components/tool-invocation-precheck.md) | `src/uaw/tool/invocation/precheck.py` |

[接口机器目录](../../../contracts/interfaces.json) · [统一对象schema](../../../contracts/uaw.schema.json)
