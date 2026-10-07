# processes.get

状态：契约0.1，待实现。类别：用户与管理端 HTTP API。所属：工作区与交付。

进程状态/日志。

[分类索引](../HTTP.md) · [统一规则](../CONVENTIONS.md) · [实际范围](../../implementation/README.md)

## 调用入口

`GET /v1/processes/{process_id}`；认证：`user`。

参数通过路径/查询传入；meta使用X-Request-Id、X-UAW-Schema-Version，DELETE还使用If-Match。不能发送模型上下文或主体字段。

## 输入

[ProcessesGetRequest](../objects/ProcessesGetRequest.md)；每个字段的类型、必填性、默认注解、限制和分支见对象页。

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `process_id` | [ID](../objects/ID.md) | 是 | 进程 |
| `cursor` | [Cursor](../objects/Cursor.md) | 否 | 增量 |

## 输出

[HttpProcessesGetResult](../objects/HttpProcessesGetResult.md) 为完整返回结构。`kind=ok` 的payload是 [ProcessRecord](../objects/ProcessRecord.md)。`waiting`带wait_ref，其他非成功状态带Failure，不能用空对象假装成功。

| payload字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `id` | [ID](../objects/ID.md) | 是 | 进程 |
| `spec` | [ProcessSpec](../objects/ProcessSpec.md) | 是 | 实际配置 |
| `status` | [ProcessState](../objects/ProcessState.md) | 是 | 进程状态 |
| `started_at` | [Timestamp](../objects/Timestamp.md) | 是 | 启动时间 |
| `ended_at` | [Timestamp](../objects/Timestamp.md) | 否 | 结束时间 |
| `exit_code` | [ExitCode](../objects/ExitCode.md) | 否 | 真实退出码；未结束缺省 |
| `stdout_ref` | [Ref](../objects/Ref.md) | 否 | 输出内容 |
| `stderr_ref` | [Ref](../objects/Ref.md) | 否 | 错误输出 |
| `output_cursor` | [Cursor](../objects/Cursor.md) | 否 | 未读日志 |
| `change_set_ref` | [Ref](../objects/Ref.md) | 否 | 命令造成的改动 |
| `failure` | [Failure](../objects/Failure.md) | 否 | 启动/终止失败 |

## 约束与提交

- 效果分类：`read`。
- 认证/上下文：`user`；范围及权限由服务端或Runner取得。
- 请求/动作ID去重与CAS按[统一规则](../CONVENTIONS.md)执行，重复ID不同参数必须冲突。
- 功能旗标：`process_exec`；关闭时发现不展示，直接调用/恢复也拒绝。


## 错误、等待、取消

错误对象是 [Failure](../objects/Failure.md)；统一分类：schema_invalid / permission_denied / feature_disabled / revision_conflict / stale_resource / dependency_unavailable / budget_exceeded / deadline_exceeded / cancelled / unknown_effect。实际Runtime需要把业务错误映射到此对象；上述分类不会代替明确failed_phase和恢复提示。

只读可在有界策略内重试；写失败先核对动作账本，效果unknown时禁止盲重试；waiting通过审批决定、用户输入、process.poll或agents.wait推进。取消只停止后续执行，已有效果如实保留。

## 请求示例

示例展示结构；不代表这些示例引用存在。

```json
{
  "process_id": "example_001"
}
```

## 成功结构示例

```json
{
  "kind": "ok",
  "payload": {
    "id": "example_001",
    "spec": {
      "workspace_ref": {
        "kind": "web",
        "id": "example_001",
        "version": "example_001"
      },
      "executable": "example_001",
      "argv": [],
      "cwd": "src/main.py",
      "environment": [],
      "timeout_ms": 1
    },
    "status": "starting",
    "started_at": "2026-10-07T02:00:00Z"
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
| `workspace.process` | [开发设计](../../../docs/design/components/workspace-process.md) | `src/uaw/workspace/process.py` |

[接口机器目录](../../../contracts/interfaces.json) · [统一对象schema](../../../contracts/uaw.schema.json)
