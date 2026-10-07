# processes.stop

状态：契约0.1，待实现。类别：用户与管理端 HTTP API。所属：工作区与交付。

停止进程树。

[分类索引](../HTTP.md) · [统一规则](../CONVENTIONS.md) · [实际范围](../../implementation/README.md)

## 调用入口

`POST /v1/processes/{process_id}/stop`；认证：`user`。

请求体是 `{meta, payload}`；路径ID从path取得，不重复写入payload。OpenAPI记录实际线上字段位置；下方输入对象是服务合成的业务请求。

## 输入

[ProcessesStopRequest](../objects/ProcessesStopRequest.md)；每个字段的类型、必填性、默认注解、限制和分支见对象页。

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `process_id` | [ID](../objects/ID.md) | 是 | 进程 |
| `reason` | [NonEmptyText](../objects/NonEmptyText.md) | 是 | 理由 |

## 输出

[HttpProcessesStopResult](../objects/HttpProcessesStopResult.md) 为完整返回结构。`kind=ok` 的payload是 [ProcessRecord](../objects/ProcessRecord.md)。`waiting`带wait_ref，其他非成功状态带Failure，不能用空对象假装成功。

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

- 效果分类：`process`。
- 认证/上下文：`user`；范围及权限由服务端或Runner取得。
- 请求/动作ID去重与CAS按[统一规则](../CONVENTIONS.md)执行，重复ID不同参数必须冲突。
- 功能旗标：`process_exec`；关闭时发现不展示，直接调用/恢复也拒绝。
- 先软终止、超时硬终止；离线lost不伪称stopped。

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
    "reason": "example_001"
  }
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
| `workspace.process` | [开发设计](../../../docs/design/components/workspace-process.md) | `src/uaw/workspace/process.py` |
| `run.cancel` | [开发设计](../../../docs/design/components/run-cancel.md) | `src/uaw/run/cancel.py` |

[接口机器目录](../../../contracts/interfaces.json) · [统一对象schema](../../../contracts/uaw.schema.json)
