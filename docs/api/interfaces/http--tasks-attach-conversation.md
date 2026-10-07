# tasks.attach_conversation

状态：契约0.1，待实现。类别：用户与管理端 HTTP API。所属：运行与会话。

显式把同用户另一会话关联到现有任务。

[分类索引](../HTTP.md) · [统一规则](../CONVENTIONS.md) · [实际范围](../../implementation/README.md)

## 调用入口

`POST /v1/tasks/{task_id}/conversations`；认证：`user`。

请求体是 `{meta, payload}`；路径ID从path取得，不重复写入payload。OpenAPI记录实际线上字段位置；下方输入对象是服务合成的业务请求。

## 输入

[TasksAttach_conversationRequest](../objects/TasksAttach_conversationRequest.md)；每个字段的类型、必填性、默认注解、限制和分支见对象页。

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `task_id` | [ID](../objects/ID.md) | 是 | 共享任务 |
| `conversation_id` | [ID](../objects/ID.md) | 是 | 目标会话 |
| `source_input_ref` | [UserInputRef](../objects/UserInputRef.md) | 是 | 用户明确关联要求 |

## 输出

[HttpTasksAttachConversationResult](../objects/HttpTasksAttachConversationResult.md) 为完整返回结构。`kind=ok` 的payload是 [TaskRecord](../objects/TaskRecord.md)。`waiting`带wait_ref，其他非成功状态带Failure，不能用空对象假装成功。

| payload字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `id` | [ID](../objects/ID.md) | 是 | 任务 |
| `revision` | [Revision](../objects/Revision.md) | 是 | 目标版本 |
| `conversation_refs` | 数组&lt;[Ref](../objects/Ref.md)&gt; | 是 | 关联会话 |
| `frame_ref` | [Ref](../objects/Ref.md) | 否 | 正式理解 |
| `active_run_refs` | 数组&lt;[Ref](../objects/Ref.md)&gt; | 是 | 运行 |
| `artifact_refs` | 数组&lt;[Ref](../objects/Ref.md)&gt; | 是 | 成果 |
| `created_at` | [Timestamp](../objects/Timestamp.md) | 是 | 创建时间 |

## 约束与提交

- 效果分类：`internal_write`。
- 认证/上下文：`user`；范围及权限由服务端或Runner取得。
- 请求/动作ID去重与CAS按[统一规则](../CONVENTIONS.md)执行，重复ID不同参数必须冲突。
- 两端同主体且expected_revision匹配；关联不复制权限，不取得写控制权；并发修订CAS冲突。
- HTTP meta.expected_revision必填且≥1；过期提交返回conflict，不能自动覆盖。

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
    "expected_revision": 3
  },
  "payload": {
    "conversation_id": "example_001",
    "source_input_ref": {
      "kind": "input",
      "id": "example_001",
      "version": "example_001"
    }
  }
}
```

## 成功结构示例

```json
{
  "kind": "ok",
  "payload": {
    "id": "example_001",
    "revision": 0,
    "conversation_refs": [],
    "active_run_refs": [],
    "artifact_refs": [],
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
| `run.history` | [开发设计](../../../docs/design/components/run-history.md) | `src/uaw/run/history.py` |
| `agent.board` | [开发设计](../../../docs/design/components/agent-board.md) | `src/uaw/agent/board.py` |
| `run.state` | [开发设计](../../../docs/design/components/run-state.md) | `src/uaw/run/state.py` |

[接口机器目录](../../../contracts/interfaces.json) · [统一对象schema](../../../contracts/uaw.schema.json)
