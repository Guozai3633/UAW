# context.memory.policy

状态：契约0.1，待实现。类别：细分组件私有接口。所属：上下文与资料。

范围与写入政策的私有阶段输入。

[分类索引](../COMPONENT.md) · [统一规则](../CONVENTIONS.md) · [实际范围](../../implementation/README.md)

## 调用入口

计划Python异步签名：`async def handle(request: InternalContextMemoryPolicyRequest, context: TrustedExecutionContext) -> ComponentContextMemoryPolicyResult`。所属入口为 `context.memory.policy`。该签名是契约目标；实际方法定位见对应开发设计，不能从公网/LLM直接调用私有组件。

## 输入

[InternalContextMemoryPolicyRequest](../objects/InternalContextMemoryPolicyRequest.md)；每个字段的类型、必填性、默认注解、限制和分支见对象页。

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `memory_policy_ref` | [Ref](../objects/Ref.md) | 是 | 当前记忆读取/贡献/范围/保留政策。 |
| `candidate_ref` | [Ref](../objects/Ref.md) | 是 | 尚未确认的记忆/结果候选版本。 |
| `target_scope` | [Scope](../objects/Scope.md) | 是 | 候选记忆/资源生效范围，只能在当前权限内缩小。 |
| `retention` | [Duration](../objects/Duration.md) | 否 | 记忆保留毫秒数，最终由有效政策限定。 |

## 输出

[ComponentContextMemoryPolicyResult](../objects/ComponentContextMemoryPolicyResult.md) 为完整返回结构。`kind=ok` 的payload是 [MemoryPolicyDecision](../objects/MemoryPolicyDecision.md)。`waiting`带wait_ref，其他非成功状态带Failure，不能用空对象假装成功。

| payload字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `allowed` | [Bool](../objects/Bool.md) | 是 | 是否允许 |
| `effective_scope` | [Scope](../objects/Scope.md) | 是 | 最终范围 |
| `expires_at` | [Timestamp](../objects/Timestamp.md) | 否 | 期限 |
| `reason` | [NonEmptyText](../objects/NonEmptyText.md) | 是 | 依据 |

## 约束与提交

- 效果分类：`read`。
- 认证/上下文：`service`；范围及权限由服务端或Runner取得。
- 请求/动作ID去重与CAS按[统一规则](../CONVENTIONS.md)执行，重复ID不同参数必须冲突。
- 政策版本记录，不把候选文字当授权。
- 检查读/贡献开关与用户要求
- 核对内容敏感范围、用途与保留
- 确定仅任务/会话/用户范围
- 拒绝或返回允许的写入范围给冲突检查
- 取消/超时遵从COMMON_CONTRACTS；所有引用必须当前权限内、版本可访问。

## 错误、等待、取消

- 关闭贡献不写
- 共享范围无权拒绝

错误对象是 [Failure](../objects/Failure.md)；统一分类：schema_invalid / permission_denied / feature_disabled / revision_conflict / stale_resource / dependency_unavailable / budget_exceeded / deadline_exceeded / cancelled / unknown_effect。实际Runtime需要把业务错误映射到此对象；上述分类不会代替明确failed_phase和恢复提示。

只读可在有界策略内重试；写失败先核对动作账本，效果unknown时禁止盲重试；waiting通过审批决定、用户输入、process.poll或agents.wait推进。取消只停止后续执行，已有效果如实保留。

## 请求示例

示例展示结构；不代表这些示例引用存在。

```json
{
  "memory_policy_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "candidate_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "target_scope": {
    "principal_id": "example_001"
  }
}
```

## 成功结构示例

```json
{
  "kind": "ok",
  "payload": {
    "allowed": true,
    "effective_scope": {
      "principal_id": "example_001"
    },
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
| `context.memory.policy` | [开发设计](../../../docs/design/components/context-memory-policy.md) | `src/uaw/context/memory/policy.py` |

[接口机器目录](../../../contracts/interfaces.json) · [统一对象schema](../../../contracts/uaw.schema.json)
