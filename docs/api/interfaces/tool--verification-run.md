# verification.run

状态：契约0.1，待实现。类别：模型可调用工具。所属：工作区与交付。

执行一个批准的检查命令。

[分类索引](../TOOL.md) · [统一规则](../CONVENTIONS.md) · [实际范围](../../implementation/README.md)

## 调用入口

LLM提出 `verification.run(arguments)` → ToolRuntime校验/权限/必要审批 → `workspace`负责人。ToolRuntime注入可信上下文，业务参数只使用下方输入结构。

## 输入

[ToolVerificationRunInput](../objects/ToolVerificationRunInput.md)；每个字段的类型、必填性、默认注解、限制和分支见对象页。

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `spec` | [ProcessSpec](../objects/ProcessSpec.md) | 是 | 检查命令 |
| `requirement_ids` | 数组&lt;[ID](../objects/ID.md)&gt; | 是 | 覆盖要求 |

## 输出

[ToolVerificationRunResult](../objects/ToolVerificationRunResult.md) 为完整返回结构。`kind=ok` 的payload是 [VerificationCheck](../objects/VerificationCheck.md)。`waiting`带wait_ref，其他非成功状态带Failure，不能用空对象假装成功。

| payload字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `id` | [ID](../objects/ID.md) | 是 | 检查 |
| `kind` | [VerificationKind](../objects/VerificationKind.md) | 是 | 命令/结构/引用/语义 |
| `requirement_ids` | 数组&lt;[ID](../objects/ID.md)&gt; | 是 | 覆盖要求 |
| `state` | [CheckState](../objects/CheckState.md) | 是 | passed/failed/not_run/blocked |
| `target_refs` | 数组&lt;[Ref](../objects/Ref.md)&gt; | 是 | 核验版本 |
| `process_ref` | [Ref](../objects/Ref.md) | 否 | 命令检查必需 |
| `evidence_refs` | 数组&lt;[Ref](../objects/Ref.md)&gt; | 是 | 真实证据 |
| `summary` | [Text](../objects/Text.md) | 是 | 解释及限制 |

## 约束与提交

- 效果分类：`process`。
- 认证/上下文：`agent`；范围及权限由服务端或Runner取得。
- 请求/动作ID去重与CAS按[统一规则](../CONVENTIONS.md)执行，重复ID不同参数必须冲突。
- 功能旗标：`process_exec`；关闭时发现不展示，直接调用/恢复也拒绝。
- 进程仍运行时返回waiting；结束证据含exit_code及输出；命令退出0只说明该检查通过。

## 错误、等待、取消

错误对象是 [Failure](../objects/Failure.md)；统一分类：schema_invalid / permission_denied / feature_disabled / revision_conflict / stale_resource / dependency_unavailable / budget_exceeded / deadline_exceeded / cancelled / unknown_effect。实际Runtime需要把业务错误映射到此对象；上述分类不会代替明确failed_phase和恢复提示。

只读可在有界策略内重试；写失败先核对动作账本，效果unknown时禁止盲重试；waiting通过审批决定、用户输入、process.poll或agents.wait推进。取消只停止后续执行，已有效果如实保留。

## 请求示例

示例展示结构；不代表这些示例引用存在。

```json
{
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
  "requirement_ids": []
}
```

## 成功结构示例

```json
{
  "kind": "ok",
  "payload": {
    "id": "example_001",
    "kind": "command",
    "requirement_ids": [],
    "state": "passed",
    "target_refs": [],
    "evidence_refs": [
      {
        "kind": "web",
        "id": "example_001",
        "version": "example_001"
      }
    ],
    "summary": "example_001",
    "process_ref": {
      "kind": "web",
      "id": "example_001",
      "version": "example_001"
    }
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
| `agent.completion.evidence` | [开发设计](../../../docs/design/components/agent-completion-evidence.md) | `src/uaw/agent/completion/evidence.py` |

[接口机器目录](../../../contracts/interfaces.json) · [统一对象schema](../../../contracts/uaw.schema.json)
