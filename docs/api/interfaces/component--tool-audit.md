# tool.audit

状态：契约0.1，待实现。类别：细分组件私有接口。所属：工具运行。

执行审计与指标的私有阶段输入。

[分类索引](../COMPONENT.md) · [统一规则](../CONVENTIONS.md) · [实际范围](../../implementation/README.md)

## 调用入口

计划Python异步签名：`async def handle(request: InternalToolAuditRequest, context: TrustedExecutionContext) -> ComponentToolAuditResult`。所属入口为 `tool.audit`。该签名是契约目标；实际方法定位见对应开发设计，不能从公网/LLM直接调用私有组件。

## 输入

[InternalToolAuditRequest](../objects/InternalToolAuditRequest.md)；每个字段的类型、必填性、默认注解、限制和分支见对象页。

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `call_ref` | [Ref](../objects/Ref.md) | 是 | 实际调用记录及固定参数版本。 |
| `approval_ref` | [Ref](../objects/Ref.md) | 否 | 参数和资源版本匹配、未过期的授权依据。 |
| `actor` | [Principal](../objects/Principal.md) | 是 | 由可信认证产生的操作主体，不能由模型正文自报。 |
| `effect_state` | [EffectState](../objects/EffectState.md) | 是 | 外部效果confirmed/pending/unknown，不能凭HTTP200推断。 |
| `usage` | [Usage](../objects/Usage.md) | 是 | 全部真实attempt消耗，账单不确定性显式记录。 |

## 输出

[ComponentToolAuditResult](../objects/ComponentToolAuditResult.md) 为完整返回结构。`kind=ok` 的payload是 [AuditRecord](../objects/AuditRecord.md)。`waiting`带wait_ref，其他非成功状态带Failure，不能用空对象假装成功。

| payload字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `id` | [ID](../objects/ID.md) | 是 | 记录 |
| `actor` | [Principal](../objects/Principal.md) | 是 | 真实主体 |
| `call_ref` | [Ref](../objects/Ref.md) | 是 | 调用 |
| `approval_ref` | [Ref](../objects/Ref.md) | 否 | 授权依据 |
| `effect_state` | [EffectState](../objects/EffectState.md) | 是 | 真实效果 |
| `usage_ref` | [Ref](../objects/Ref.md) | 是 | 尝试用量 |
| `created_at` | [Timestamp](../objects/Timestamp.md) | 是 | 时间 |

## 约束与提交

- 效果分类：`read`。
- 认证/上下文：`service`；范围及权限由服务端或Runner取得。
- 请求/动作ID去重与CAS按[统一规则](../CONVENTIONS.md)执行，重复ID不同参数必须冲突。
- 关键审计不可采样丢失；Trace可按政策采样，二者用调用ID关联。
- 从实际调用取主体、动作、版本、批准依据和时间
- 记录尝试/结果/效果状态及数据引用
- 对敏感字段脱敏并保持授权诊断入口
- 向Run追加必要交互/审计事件，向Observability报告诊断span
- 审计必需动作在落盘失败时停下
- 取消/超时遵从COMMON_CONTRACTS；所有引用必须当前权限内、版本可访问。

## 错误、等待、取消

- 普通观测故障不回滚已完成外部效果
- 审计必需且不可写返回audit_unavailable
- 缺关联标识拒绝不明调用

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
  "actor": {
    "id": "example_001",
    "kind": "user",
    "auth_session_id": "example_001"
  },
  "effect_state": "confirmed",
  "usage": {
    "attempt_id": "example_001",
    "resources": {
      "model_calls": 0,
      "tool_calls": 0,
      "child_agents": 0,
      "wall_time_ms": 0,
      "currency": "CNY",
      "input_tokens": 0,
      "output_tokens": 0,
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
    "id": "example_001",
    "actor": {
      "id": "example_001",
      "kind": "user",
      "auth_session_id": "example_001"
    },
    "call_ref": {
      "kind": "web",
      "id": "example_001",
      "version": "example_001"
    },
    "effect_state": "confirmed",
    "usage_ref": {
      "kind": "web",
      "id": "example_001",
      "version": "example_001"
    },
    "created_at": "2026-10-07T02:00:00Z"
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
| `tool.audit` | [开发设计](../../../docs/design/components/tool-audit.md) | `src/uaw/tool/audit.py` |

[接口机器目录](../../../contracts/interfaces.json) · [统一对象schema](../../../contracts/uaw.schema.json)
