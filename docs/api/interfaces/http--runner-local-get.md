# runner.local.get

状态：已实现本机开发控制层；Agent执行尚未接入。类别：用户与管理端 HTTP API。所属：运行与会话。

查询原本机启动；当前主体/通道/原根复查，后端重启标unavailable，不重发。

[分类索引](../HTTP.md) · [统一规则](../CONVENTIONS.md) · [实际范围](../../implementation/README.md)

## 调用入口

`GET /v1/runner/local/{launch_id}`；认证：`user`。

参数通过路径/查询传入；meta使用X-Request-Id、X-UAW-Schema-Version，DELETE还使用If-Match。不能发送模型上下文或主体字段。

## 输入

[RunnerLocalGetRequest](../objects/RunnerLocalGetRequest.md)；每个字段的类型、必填性、默认注解、限制和分支见对象页。

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `launch_id` | [ID](../objects/ID.md) | 是 | 原启动 |

## 输出

[HttpRunnerLocalGetResult](../objects/HttpRunnerLocalGetResult.md) 为完整返回结构。`kind=ok` 的payload是 [InstalledLaunchView](../objects/InstalledLaunchView.md)。`waiting`带wait_ref，其他非成功状态带Failure，不能用空对象假装成功。

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

- 效果分类：`read`。
- 认证/上下文：`user`；范围及权限由服务端或Runner取得。
- 请求/动作ID去重与CAS按[统一规则](../CONVENTIONS.md)执行，重复ID不同参数必须冲突。
- 同账号新Web session不能接管旧实例；状态不替代Tool/预算/RootSource。

## 错误、等待、取消

错误对象是 [Failure](../objects/Failure.md)；统一分类：schema_invalid / permission_denied / feature_disabled / revision_conflict / stale_resource / dependency_unavailable / budget_exceeded / deadline_exceeded / cancelled / unknown_effect。实际Runtime需要把业务错误映射到此对象；上述分类不会代替明确failed_phase和恢复提示。

只读可在有界策略内重试；写失败先核对动作账本，效果unknown时禁止盲重试；waiting通过审批决定、用户输入、process.poll或agents.wait推进。取消只停止后续执行，已有效果如实保留。

## 请求示例

示例展示结构；不代表这些示例引用存在。

```json
{
  "launch_id": "example_001"
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
| `workspace.binding` | [开发设计](../../../docs/design/components/workspace-binding.md) | `src/uaw/workspace/binding.py` |

[接口机器目录](../../../contracts/interfaces.json) · [统一对象schema](../../../contracts/uaw.schema.json)
