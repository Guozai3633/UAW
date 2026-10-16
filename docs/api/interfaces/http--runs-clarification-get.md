# runs.clarification.get

状态：已实现本机开发控制层；Agent执行尚未接入。类别：用户与管理端 HTTP API。所属：运行与会话。

读取原Run特定问题，不猜最新问题。

[分类索引](../HTTP.md) · [统一规则](../CONVENTIONS.md) · [实际范围](../../implementation/README.md)

## 调用入口

`GET /v1/runs/{run_id}/clarifications/{question_item_id}`；认证：`user`。

参数通过路径/查询传入；meta使用X-Request-Id、X-UAW-Schema-Version，DELETE还使用If-Match。不能发送模型上下文或主体字段。

## 输入

[RunClarificationGetRequest](../objects/RunClarificationGetRequest.md)；每个字段的类型、必填性、默认注解、限制和分支见对象页。

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `run_id` | [ID](../objects/ID.md) | 是 | 路径原Run |
| `question_item_id` | [ID](../objects/ID.md) | 是 | 路径原问题 |

## 输出

[HttpRunsClarificationGetResult](../objects/HttpRunsClarificationGetResult.md) 为完整返回结构。`kind=ok` 的payload是 [ClarificationView](../objects/ClarificationView.md)。`waiting`带wait_ref，其他非成功状态带Failure，不能用空对象假装成功。

| payload字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `question` | [ClarificationQuestion](../objects/ClarificationQuestion.md) | 是 | 当前实际问题 |
| `run_revision` | [Revision](../objects/Revision.md) | 是 | 当前Run版本，用于提交CAS |
| `run_status` | [RunStatus](../objects/RunStatus.md) | 是 | 当前Run真实状态 |
| `input_revision` | [Revision](../objects/Revision.md) | 是 | 当前有效输入版本 |

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
  "run_id": "example_001",
  "question_item_id": "example_001"
}
```

## 成功结构示例

```json
{
  "kind": "ok",
  "payload": {
    "question": {
      "protocol": "conversation-v1",
      "run_id": "example_001",
      "conversation_id": "example_001",
      "item_id": "example_001",
      "revision": 1,
      "input_revision": 1,
      "prompt": {
        "text": "example_001",
        "reason": "example_001",
        "options": []
      },
      "decision_record_ref": {
        "kind": "web",
        "id": "example_001",
        "version": "example_001"
      },
      "state": "open",
      "created_at": "2026-10-07T02:00:00Z"
    },
    "run_revision": 1,
    "run_status": "waiting_for_user",
    "input_revision": 1
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
