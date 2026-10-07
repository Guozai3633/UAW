# tool.invocation.recheck

状态：契约0.1，待实现。类别：细分组件私有接口。所属：工具运行。

执行前复核的私有阶段输入。

[分类索引](../COMPONENT.md) · [统一规则](../CONVENTIONS.md) · [实际范围](../../implementation/README.md)

## 调用入口

计划Python异步签名：`async def handle(request: InternalToolInvocationRecheckRequest, context: TrustedExecutionContext) -> ComponentToolInvocationRecheckResult`。所属入口为 `tool.invocation.recheck`。该签名是契约目标；实际方法定位见对应开发设计，不能从公网/LLM直接调用私有组件。

## 输入

[InternalToolInvocationRecheckRequest](../objects/InternalToolInvocationRecheckRequest.md)；每个字段的类型、必填性、默认注解、限制和分支见对象页。

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `call_ref` | [Ref](../objects/Ref.md) | 是 | 实际调用记录及固定参数版本。 |
| `approval_ref` | [Ref](../objects/Ref.md) | 否 | 参数和资源版本匹配、未过期的授权依据。 |
| `expected_resource_revision` | [Version](../objects/Version.md) | 是 | 调用目标当前版本必须匹配；审批后再次检查。 |

## 输出

[ComponentToolInvocationRecheckResult](../objects/ComponentToolInvocationRecheckResult.md) 为完整返回结构。`kind=ok` 的payload是 [RecheckDecision](../objects/RecheckDecision.md)。`waiting`带wait_ref，其他非成功状态带Failure，不能用空对象假装成功。

| payload字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `allowed` | [Bool](../objects/Bool.md) | 是 | 是否仍允许 |
| `validated_call_ref` | [Ref](../objects/Ref.md) | 是 | 调用 |
| `resource_refs` | 数组&lt;[Ref](../objects/Ref.md)&gt; | 是 | 最新匹配资源 |
| `approval_ref` | [Ref](../objects/Ref.md) | 否 | 授权 |
| `reason` | [NonEmptyText](../objects/NonEmptyText.md) | 是 | 依据 |

## 约束与提交

- 效果分类：`read`。
- 认证/上下文：`service`；范围及权限由服务端或Runner取得。
- 请求/动作ID去重与CAS按[统一规则](../CONVENTIONS.md)执行，重复ID不同参数必须冲突。
- 保存实际复核policy revision与结果。
- 重新读取当前身份与撤销
- 比较实际参数hash和审批绑定
- 核对资源版本/有效期/受限持续授权谓词
- 通过才签执行所需短期上下文，变化返回重新决策
- 取消/超时遵从COMMON_CONTRACTS；所有引用必须当前权限内、版本可访问。

## 错误、等待、取消

- approval_stale重新申请或解释
- 当前撤销直接拒绝

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
  "expected_resource_revision": "example_001"
}
```

## 成功结构示例

```json
{
  "kind": "ok",
  "payload": {
    "allowed": true,
    "validated_call_ref": {
      "kind": "web",
      "id": "example_001",
      "version": "example_001"
    },
    "resource_refs": [],
    "reason": "example_001"
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
| `tool.invocation.recheck` | [开发设计](../../../docs/design/components/tool-invocation-recheck.md) | `src/uaw/tool/invocation/recheck.py` |

[接口机器目录](../../../contracts/interfaces.json) · [统一对象schema](../../../contracts/uaw.schema.json)
