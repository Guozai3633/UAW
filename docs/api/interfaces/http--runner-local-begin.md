# runner.local.begin

状态：已实现本机开发控制层；Agent执行尚未接入。类别：用户与管理端 HTTP API。所属：运行与会话。

当前Web用户请求本机本人确认；异步返回原启动状态。

[分类索引](../HTTP.md) · [统一规则](../CONVENTIONS.md) · [实际范围](../../implementation/README.md)

## 调用入口

`POST /v1/runner/local`；认证：`user`。

请求体是 `{meta, payload}`；路径ID从path取得，不重复写入payload。OpenAPI记录实际线上字段位置；下方输入对象是服务合成的业务请求。

## 输入

[RunnerLocalBeginRequest](../objects/RunnerLocalBeginRequest.md)；每个字段的类型、必填性、默认注解、限制和分支见对象页。

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |

## 输出

[HttpRunnerLocalBeginResult](../objects/HttpRunnerLocalBeginResult.md) 为完整返回结构。`kind=ok` 的payload是 [InstalledLaunchView](../objects/InstalledLaunchView.md)。`waiting`带wait_ref，其他非成功状态带Failure，不能用空对象假装成功。

| payload字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `id` | [ID](../objects/ID.md) | 是 | 原启动身份 |
| `request_id` | [ID](../objects/ID.md) | 是 | 原RequestMeta.request_id |
| `revision` | [Revision](../objects/Revision.md) | 是 | 状态持久CAS版本 |
| `state` | enum: `starting` / `waiting_device` / `connecting` / `selecting_directory` / `ready` / `closed` / `failed` / `unavailable` | 是 | 实际生命周期 |
| `workspace_ref` | [Ref](../objects/Ref.md) | 是 | 管理员安装配置中的逻辑工作区；不是本机路径 |
| `created_at` | [Timestamp](../objects/Timestamp.md) | 是 | 原启动时间 |
| `updated_at` | [Timestamp](../objects/Timestamp.md) | 是 | 本次状态时间 |
| `enrollment_id` | [ID](../objects/ID.md) | 否 | 原设备登记 |
| `device_ref` | [Ref](../objects/Ref.md) | 否 | 当前实际通道绑定的设备版本与摘要 |
| `expires_at` | [Timestamp](../objects/Timestamp.md) | 否 | 原通道期限，不从轮询重新计时 |
| `failure_code` | [ID](../objects/ID.md) | 否 | 有界错误码；不输出路径/proof/凭据 |

## 约束与提交

- 效果分类：`internal_write`。
- 认证/上下文：`user`；范围及权限由服务端或Runner取得。
- 请求/动作ID去重与CAS按[统一规则](../CONVENTIONS.md)执行，重复ID不同参数必须冲突。
- 精确Origin/cookie/CSRF；payload为空，不接路径/approved/owner/module/key。部署缺源503；最多一个自有实例。相同原会话/request_id只查询原历史，不重弹窗。HTTP成功202不是授权成功。

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
  "payload": {}
}
```

## 成功结构示例

```json
{
  "kind": "ok",
  "payload": {
    "id": "example_001",
    "request_id": "example_001",
    "revision": 0,
    "state": "starting",
    "workspace_ref": {
      "kind": "web",
      "id": "example_001",
      "version": "example_001"
    },
    "created_at": "2026-10-07T02:00:00Z",
    "updated_at": "2026-10-07T02:00:00Z"
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
| `workspace.binding` | [开发设计](../../../docs/design/components/workspace-binding.md) | `src/uaw/workspace/binding.py` |

[接口机器目录](../../../contracts/interfaces.json) · [统一对象schema](../../../contracts/uaw.schema.json)
