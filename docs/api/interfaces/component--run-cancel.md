# run.cancel

状态：契约0.1，待实现。类别：细分组件私有接口。所属：运行与会话。

取消树并保留成果。

[分类索引](../COMPONENT.md) · [统一规则](../CONVENTIONS.md) · [实际范围](../../implementation/README.md)

## 调用入口

计划Python异步签名：`async def handle(request: CancelInternalRequest, context: TrustedExecutionContext) -> ComponentRunCancelResult`。所属入口为 `run.cancel`。该签名是契约目标；实际方法定位见对应开发设计，不能从公网/LLM直接调用私有组件。

## 输入

[CancelInternalRequest](../objects/CancelInternalRequest.md)；每个字段的类型、必填性、默认注解、限制和分支见对象页。

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `target_run_ref` | [Ref](../objects/Ref.md) | 是 | 运行 |
| `target_agent_refs` | 数组&lt;[Ref](../objects/Ref.md)&gt; | 否 | 子树 |
| `reason` | [NonEmptyText](../objects/NonEmptyText.md) | 是 | 原因 |
| `preserve_artifact_refs` | 数组&lt;[Ref](../objects/Ref.md)&gt; | 是 | 保留 |

## 输出

[ComponentRunCancelResult](../objects/ComponentRunCancelResult.md) 为完整返回结构。`kind=ok` 的payload是 [CancellationResult](../objects/CancellationResult.md)。`waiting`带wait_ref，其他非成功状态带Failure，不能用空对象假装成功。

| payload字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `target_refs` | 数组&lt;[Ref](../objects/Ref.md)&gt; | 是 | 目标 |
| `stopped_refs` | 数组&lt;[Ref](../objects/Ref.md)&gt; | 是 | 已停止 |
| `pending_refs` | 数组&lt;[Ref](../objects/Ref.md)&gt; | 是 | 仍处理中 |
| `unknown_effect_refs` | 数组&lt;[Ref](../objects/Ref.md)&gt; | 是 | 未确认效果 |
| `preserved_refs` | 数组&lt;[Ref](../objects/Ref.md)&gt; | 是 | 保留成果 |

## 约束与提交

- 效果分类：`read`。
- 认证/上下文：`service`；范围及权限由服务端或Runner取得。
- 请求/动作ID去重与CAS按[统一规则](../CONVENTIONS.md)执行，重复ID不同参数必须冲突。
- cancel_requested与执行器实际取消分别记录，cancelled不能掩盖外部未决效果。
- 先持久取消请求并停止新节点调度
- 递归通知子Agent、Tool调用和Workspace进程
- 有界等待可取消执行器确认，再按能力强停
- 不能取消的外部动作继续独立对账
- 保留已确认产物并返回实际停止/仍在执行/unknown列表
- 取消/超时遵从COMMON_CONTRACTS；所有引用必须当前权限内、版本可访问。

## 错误、等待、取消

- 已终止请求幂等返回
- 停止进程失败标still_running
- 缺权限不能取消别的会话Run

错误对象是 [Failure](../objects/Failure.md)；统一分类：schema_invalid / permission_denied / feature_disabled / revision_conflict / stale_resource / dependency_unavailable / budget_exceeded / deadline_exceeded / cancelled / unknown_effect。实际Runtime需要把业务错误映射到此对象；上述分类不会代替明确failed_phase和恢复提示。

只读可在有界策略内重试；写失败先核对动作账本，效果unknown时禁止盲重试；waiting通过审批决定、用户输入、process.poll或agents.wait推进。取消只停止后续执行，已有效果如实保留。

## 请求示例

示例展示结构；不代表这些示例引用存在。

```json
{
  "target_run_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "reason": "example_001",
  "preserve_artifact_refs": []
}
```

## 成功结构示例

```json
{
  "kind": "ok",
  "payload": {
    "target_refs": [],
    "stopped_refs": [],
    "pending_refs": [],
    "unknown_effect_refs": [],
    "preserved_refs": []
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
| `run.cancel` | [开发设计](../../../docs/design/components/run-cancel.md) | `src/uaw/run/cancel.py` |

[接口机器目录](../../../contracts/interfaces.json) · [统一对象schema](../../../contracts/uaw.schema.json)
