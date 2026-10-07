# turns.submit

状态：已实现本机开发控制层；Agent执行尚未接入。类别：用户与管理端 HTTP API。所属：运行与会话。

提交原文并受理Run。

[分类索引](../HTTP.md) · [统一规则](../CONVENTIONS.md) · [实际范围](../../implementation/README.md)

## 调用入口

`POST /v1/conversations/{conversation_id}/turns`；认证：`user`。

请求体是 `{meta, payload}`；路径ID从path取得，不重复写入payload。OpenAPI记录实际线上字段位置；下方输入对象是服务合成的业务请求。

## 输入

[TurnsSubmitRequest](../objects/TurnsSubmitRequest.md)；每个字段的类型、必填性、默认注解、限制和分支见对象页。

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `conversation_id` | [ID](../objects/ID.md) | 是 | 会话 |
| `text` | [Text](../objects/Text.md) | 是 | 用户原文 |
| `attachment_refs` | 数组&lt;[Ref](../objects/Ref.md)&gt; | 是 | 附件 |
| `task_id` | [ID](../objects/ID.md) | 否 | 继续已有任务 |
| `expected_task_revision` | [Revision](../objects/Revision.md) | 否 | 继续任务必需 |
| `budget` | [Budget](../objects/Budget.md) | 否 | 用户预算上限 |

## 输出

[HttpTurnsSubmitResult](../objects/HttpTurnsSubmitResult.md) 为完整返回结构。`kind=ok` 的payload是 [RunRecord](../objects/RunRecord.md)。`waiting`带wait_ref，其他非成功状态带Failure，不能用空对象假装成功。

| payload字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `id` | [ID](../objects/ID.md) | 是 | Run |
| `task_id` | [ID](../objects/ID.md) | 是 | 任务 |
| `conversation_id` | [ID](../objects/ID.md) | 是 | 入口会话 |
| `revision` | [Revision](../objects/Revision.md) | 是 | 状态版本 |
| `status` | [RunStatus](../objects/RunStatus.md) | 是 | 当前状态 |
| `root_agent_ref` | [Ref](../objects/Ref.md) | 否 | 根实例 |
| `frame_ref` | [Ref](../objects/Ref.md) | 否 | 当前任务理解 |
| `plan_ref` | [Ref](../objects/Ref.md) | 否 | 可选图 |
| `budget` | [Budget](../objects/Budget.md) | 是 | 上限 |
| `outcome` | [Outcome](../objects/Outcome.md) | 否 | 终态 |
| `created_at` | [Timestamp](../objects/Timestamp.md) | 是 | 受理时间 |
| `ended_at` | [Timestamp](../objects/Timestamp.md) | 否 | 实际结束 |

## 约束与提交

- 效果分类：`internal_write`。
- 认证/上下文：`user`；范围及权限由服务端或Runner取得。
- 请求/动作ID去重与CAS按[统一规则](../CONVENTIONS.md)执行，重复ID不同参数必须冲突。
- 同request_id+相同规范请求重放返回原Run；同键不同原文冲突；输入正文或附件至少一个非空。

## 错误、等待、取消

错误对象是 [Failure](../objects/Failure.md)；统一分类：schema_invalid / permission_denied / feature_disabled / revision_conflict / stale_resource / dependency_unavailable / budget_exceeded / deadline_exceeded / cancelled / unknown_effect。实际Runtime需要把业务错误映射到此对象；上述分类不会代替明确failed_phase和恢复提示。

只读可在有界策略内重试；写失败先核对动作账本，效果unknown时禁止盲重试；waiting通过审批决定、用户输入、process.poll或agents.wait推进。取消只停止后续执行，已有效果如实保留。

## 请求示例

示例展示结构；不代表这些示例引用存在。

```json
{
  "meta": {
    "request_id": "request_001",
    "schema_version": "0.1",
    "expected_revision": 0
  },
  "payload": {
    "text": "帮我检查这次API修改的兼容性，运行已有测试，保留我的未提交修改。",
    "attachment_refs": []
  }
}
```

## 成功结构示例

```json
{
  "kind": "ok",
  "payload": {
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
| `intent.original` | [开发设计](../../../docs/design/components/intent-original.md) | `src/uaw/intent/original.py` |
| `intent.semantic` | [开发设计](../../../docs/design/components/intent-semantic.md) | `src/uaw/intent/semantic.py` |
| `intent.frame` | [开发设计](../../../docs/design/components/intent-frame.md) | `src/uaw/intent/frame.py` |
| `agent.loop` | [开发设计](../../../docs/design/components/agent-loop.md) | `src/uaw/agent/loop.py` |

[接口机器目录](../../../contracts/interfaces.json) · [统一对象schema](../../../contracts/uaw.schema.json)
