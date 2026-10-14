# runs.clarification.answer

状态：契约0.2，待实现。类别：用户与管理端 HTTP API。所属：运行与会话。

原Run回答；身份和expected_run_revision来自meta。

[分类索引](../HTTP.md) · [统一规则](../CONVENTIONS.md) · [实际范围](../../implementation/README.md)

## 调用入口

`POST /v1/runs/{run_id}/clarifications/{question_item_id}/answers`；认证：`user`。

请求体是 `{meta, payload}`；路径ID从path取得，不重复写入payload。OpenAPI记录实际线上字段位置；下方输入对象是服务合成的业务请求。

## 输入

[RunClarificationAnswerRequest](../objects/RunClarificationAnswerRequest.md)；每个字段的类型、必填性、默认注解、限制和分支见对象页。

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `run_id` | [ID](../objects/ID.md) | 是 | 路径中的原Run |
| `question_item_id` | [ID](../objects/ID.md) | 是 | 路径中原问题稳定Item |
| `expected_question_revision` | [Revision](../objects/Revision.md) | 是 | 问题预期CAS版本 |
| `expected_input_revision` | [Revision](../objects/Revision.md) | 是 | 原有效输入版本 |
| `text` | [Text](../objects/Text.md) | 是 | 用户真实回答 |
| `attachment_refs` | 数组&lt;[Ref](../objects/Ref.md)&gt; | 是 | 本人获准材料，真实权限另查 |

## 输出

[HttpRunsClarificationAnswerResult](../objects/HttpRunsClarificationAnswerResult.md) 为完整返回结构。`kind=ok` 的payload是 [RunContinuationReceipt](../objects/RunContinuationReceipt.md)。`waiting`带wait_ref，其他非成功状态带Failure，不能用空对象假装成功。

| payload字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `protocol` | 常量 `conversation-v1` | 是 | 协议 |
| `run` | [RunRecord](../objects/RunRecord.md) | 是 | 当前原Run；允许受理后又取消的查询结果 |
| `patch` | [RunInputPatch](../objects/RunInputPatch.md) | 是 | 原请求受理及生效状态 |
| `event_seq` | [Revision](../objects/Revision.md) | 是 | 最后可续持久事件序号 |

## 约束与提交

- 效果分类：`internal_write`。
- 认证/上下文：`user`；范围及权限由服务端或Runner取得。
- 请求/动作ID去重与CAS按[统一规则](../CONVENTIONS.md)执行，重复ID不同参数必须冲突。
- 尚未装配handler；契约发布不等于端点可用。旧Run无conversation-v1绑定拒绝续跑，不转换旧期限。
- 实际认证、精确Origin、CSRF与原会话归属仍必需；请求体没有可信主体、批准或授权字段。
- 受理后返回真实原Run/补充状态；当前权限/模型/预算复核和未知效果对账后才执行。
- HTTP meta.expected_revision必填且≥1；过期提交返回conflict，不能自动覆盖。

## 错误、等待、取消

- 旧协议或来源缺失明确不可用；版本冲突重读；终态/取消不能复活；unknown先对账不重发。

错误对象是 [Failure](../objects/Failure.md)；统一分类：schema_invalid / permission_denied / feature_disabled / revision_conflict / stale_resource / dependency_unavailable / budget_exceeded / deadline_exceeded / cancelled / unknown_effect。实际Runtime需要把业务错误映射到此对象；上述分类不会代替明确failed_phase和恢复提示。

只读可在有界策略内重试；写失败先核对动作账本，效果unknown时禁止盲重试；waiting通过审批决定、用户输入、process.poll或agents.wait推进。取消只停止后续执行，已有效果如实保留。

## 请求示例

示例展示结构；不代表这些示例引用存在。

```json
{
  "meta": {
    "request_id": "request_001",
    "schema_version": "0.2",
    "expected_revision": 3
  },
  "payload": {
    "expected_question_revision": 1,
    "expected_input_revision": 1,
    "text": "example_001",
    "attachment_refs": []
  }
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
    "patch": {
      "protocol": "conversation-v1",
      "run_id": "example_001",
      "conversation_id": "example_001",
      "request_id": "example_001",
      "input_ref": {
        "kind": "input",
        "id": "example_001",
        "version": "example_001"
      },
      "kind": "clarification_answer",
      "base_input_revision": 1,
      "input_revision": 1,
      "state": "accepted",
      "created_at": "2026-10-07T02:00:00Z",
      "question_item_id": "example_001",
      "question_revision": 1
    },
    "event_seq": 1
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
