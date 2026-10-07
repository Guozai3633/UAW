# process.exec

状态：契约0.1，待实现。类别：模型可调用工具。所属：工作区与交付。

启动真实命令，例如go test ./...。

[分类索引](../TOOL.md) · [统一规则](../CONVENTIONS.md) · [实际范围](../../implementation/README.md)

## 调用入口

LLM提出 `process.exec(arguments)` → ToolRuntime校验/权限/必要审批 → `workspace`负责人。ToolRuntime注入可信上下文，业务参数只使用下方输入结构。

## 输入

[ToolProcessExecInput](../objects/ToolProcessExecInput.md)；每个字段的类型、必填性、默认注解、限制和分支见对象页。

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `spec` | [ProcessSpec](../objects/ProcessSpec.md) | 是 | 实际进程参数 |

## 输出

[ToolProcessExecResult](../objects/ToolProcessExecResult.md) 为完整返回结构。`kind=ok` 的payload是 [ProcessRecord](../objects/ProcessRecord.md)。`waiting`带wait_ref，其他非成功状态带Failure，不能用空对象假装成功。

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
- 认证/上下文：`agent`；范围及权限由服务端或Runner取得。
- 请求/动作ID去重与CAS按[统一规则](../CONVENTIONS.md)执行，重复ID不同参数必须冲突。
- 功能旗标：`process_exec`；关闭时发现不展示，直接调用/恢复也拒绝。


## 错误、等待、取消

错误对象是 [Failure](../objects/Failure.md)；统一分类：schema_invalid / permission_denied / feature_disabled / revision_conflict / stale_resource / dependency_unavailable / budget_exceeded / deadline_exceeded / cancelled / unknown_effect。实际Runtime需要把业务错误映射到此对象；上述分类不会代替明确failed_phase和恢复提示。

只读可在有界策略内重试；写失败先核对动作账本，效果unknown时禁止盲重试；waiting通过审批决定、用户输入、process.poll或agents.wait推进。取消只停止后续执行，已有效果如实保留。

## 请求示例

示例展示结构；不代表这些示例引用存在。

```json
{
  "spec": {
    "workspace_ref": {
      "kind": "workspace",
      "id": "workspace_main",
      "version": "tree_7"
    },
    "executable": "go",
    "argv": [
      "test",
      "./..."
    ],
    "cwd": ".",
    "environment": [],
    "timeout_ms": 120000
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

[接口机器目录](../../../contracts/interfaces.json) · [统一对象schema](../../../contracts/uaw.schema.json)
