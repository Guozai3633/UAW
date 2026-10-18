# runs.presentation.get

状态：已实现本机开发控制层；Agent执行尚未接入。类别：用户与管理端 HTTP API。所属：运行与会话。

运行状态。

[分类索引](../HTTP.md) · [统一规则](../CONVENTIONS.md) · [实际范围](../../implementation/README.md)

## 调用入口

`GET /v1/runs/{run_id}/presentation`；认证：`user`。

参数通过路径/查询传入；meta使用X-Request-Id、X-UAW-Schema-Version，DELETE还使用If-Match。不能发送模型上下文或主体字段。

## 输入

[RunsGetRequest](../objects/RunsGetRequest.md)；每个字段的类型、必填性、默认注解、限制和分支见对象页。

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `run_id` | [ID](../objects/ID.md) | 是 | 运行 |

## 输出

[HttpRunsPresentationGetResult](../objects/HttpRunsPresentationGetResult.md) 为完整返回结构。`kind=ok` 的payload是 [RunPresentationView](../objects/RunPresentationView.md)。`waiting`带wait_ref，其他非成功状态带Failure，不能用空对象假装成功。

| payload字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `protocol` | 常量 `conversation-v1` | 是 | 协议 |
| `run` | [RunRecord](../objects/RunRecord.md) | 是 | 权威原Run，保持原CAS修订和状态 |
| `input_revision` | [Revision](../objects/Revision.md) | 是 | 当前有效输入版本 |
| `phase` | enum: `preparing` / `working` / `verifying` / `waiting_for_user` / `awaiting_acceptance` / `finalizing` / `needs_revision` / `stopping` / `completed` / `failed` / `cancelled` / `unavailable` | 是 | 显示阶段，不替代Run.status；取消受理尚未终态为stopping |
| `understanding` | [RunPresentationUnderstanding](../objects/RunPresentationUnderstanding.md) | 是 | 真实理解状态与来源 |
| `delivery` | [RunPresentationDelivery](../objects/RunPresentationDelivery.md) | 否 | 仅返回同一当前Run修订和输入的成果 |
| `stopped_reply_ref` | [Ref](../objects/Ref.md) | 否 | 原普通回复与调用已停止的证据；仅释放本地发送查询，不结算Run/费用或授权续跑 |
| `captured_at` | [Timestamp](../objects/Timestamp.md) | 是 | 一致性快照读取时间 |

## 约束与提交

- 效果分类：`read`。
- 认证/上下文：`user`；范围及权限由服务端或Runner取得。
- 请求/动作ID去重与CAS按[统一规则](../CONVENTIONS.md)执行，重复ID不同参数必须冲突。
- MS-I2m M1仅安装所属原Run控制的读取与受理handler，尚不唤醒执行；旧Run无conversation-v1绑定明确拒绝，不转换旧期限。
- 实际认证、精确Origin、CSRF与原会话归属仍必需；请求体没有可信主体、批准或授权字段。
- 受理后返回真实原Run/补充状态；当前权限/模型/预算复核和未知效果对账后才执行。

## 错误、等待、取消

- 旧协议或来源缺失明确不可用；版本冲突重读；终态/取消不能复活；unknown先对账不重发。

错误对象是 [Failure](../objects/Failure.md)；统一分类：schema_invalid / permission_denied / feature_disabled / revision_conflict / stale_resource / dependency_unavailable / budget_exceeded / deadline_exceeded / cancelled / unknown_effect。实际Runtime需要把业务错误映射到此对象；上述分类不会代替明确failed_phase和恢复提示。

只读可在有界策略内重试；写失败先核对动作账本，效果unknown时禁止盲重试；waiting通过审批决定、用户输入、process.poll或agents.wait推进。取消只停止后续执行，已有效果如实保留。

## 请求示例

示例展示结构；不代表这些示例引用存在。

```json
{
  "run_id": "example_001"
}
```

## 成功结构示例

```json
{
  "kind": "ok",
  "payload": {
    "protocol": "conversation-v1",
    "run": {
      "id": "example_001",
      "task_id": "example_001",
      "conversation_id": "example_001",
      "revision": 0,
      "status": "queued",
      "budget": {
        "limits": {
          "input_tokens": 0,
          "output_tokens": 0,
          "model_calls": 0,
          "tool_calls": 0,
          "child_agents": 0,
          "wall_time_ms": 0,
          "money": "0",
          "currency": "CNY"
        },
        "max_steps": 0,
        "max_depth": 0,
        "deadline": "2026-10-07T02:00:00Z"
      },
      "created_at": "2026-10-07T02:00:00Z"
    },
    "input_revision": 1,
    "phase": "preparing",
    "understanding": {
      "state": "pending",
      "input_revision": 1
    },
    "captured_at": "2026-10-07T02:00:00Z"
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
| `ui` | [开发设计](../../../docs/design/components/ui.md) | `apps/web/src/features/workspace/` |
| `ingress` | [开发设计](../../../docs/design/components/ingress.md) | `src/uaw/api/ingress.py` |
| `run.history` | [开发设计](../../../docs/design/components/run-history.md) | `src/uaw/run/history.py` |
| `run.state` | [开发设计](../../../docs/design/components/run-state.md) | `src/uaw/run/state.py` |
| `run.budget` | [开发设计](../../../docs/design/components/run-budget.md) | `src/uaw/run/budget.py` |

[接口机器目录](../../../contracts/interfaces.json) · [统一对象schema](../../../contracts/uaw.schema.json)
