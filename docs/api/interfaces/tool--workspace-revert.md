# workspace.revert

状态：契约0.1，待实现。类别：模型可调用工具。所属：工作区与交付。

撤销选定可逆文件改动。

[分类索引](../TOOL.md) · [统一规则](../CONVENTIONS.md) · [实际范围](../../implementation/README.md)

## 调用入口

LLM提出 `workspace.revert(arguments)` → ToolRuntime校验/权限/必要审批 → `workspace`负责人。ToolRuntime注入可信上下文，业务参数只使用下方输入结构。

## 输入

[ToolWorkspaceRevertInput](../objects/ToolWorkspaceRevertInput.md)；每个字段的类型、必填性、默认注解、限制和分支见对象页。

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `workspace_ref` | [Ref](../objects/Ref.md) | 是 | 目标版本 |
| `change_set_ref` | [Ref](../objects/Ref.md) | 是 | 变更 |
| `selected_unit_ids` | 数组&lt;[ID](../objects/ID.md)&gt; | 是 | 改动块 |
| `expected_workspace_version` | [Version](../objects/Version.md) | 是 | 当前基线 |

## 输出

[ToolWorkspaceRevertResult](../objects/ToolWorkspaceRevertResult.md) 为完整返回结构。`kind=ok` 的payload是 [MergeResult](../objects/MergeResult.md)。`waiting`带wait_ref，其他非成功状态带Failure，不能用空对象假装成功。

| payload字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `status` | [MergeStatus](../objects/MergeStatus.md) | 是 | 已合并或需冲突处理 |
| `workspace_ref` | [Ref](../objects/Ref.md) | 是 | 实际当前文件树 |
| `applied_unit_ids` | 数组&lt;[ID](../objects/ID.md)&gt; | 是 | 确实应用的块 |
| `conflict_unit_ids` | 数组&lt;[ID](../objects/ID.md)&gt; | 是 | 阻塞块 |
| `change_set_ref` | [Ref](../objects/Ref.md) | 否 | 合并结果 |
| `revalidation_required` | [Bool](../objects/Bool.md) | 是 | 旧验证是否失效 |

## 约束与提交

- 效果分类：`workspace_write`。
- 认证/上下文：`agent`；范围及权限由服务端或Runner取得。
- 请求/动作ID去重与CAS按[统一规则](../CONVENTIONS.md)执行，重复ID不同参数必须冲突。
- 功能旗标：`file_write`；关闭时发现不展示，直接调用/恢复也拒绝。


## 错误、等待、取消

错误对象是 [Failure](../objects/Failure.md)；统一分类：schema_invalid / permission_denied / feature_disabled / revision_conflict / stale_resource / dependency_unavailable / budget_exceeded / deadline_exceeded / cancelled / unknown_effect。实际Runtime需要把业务错误映射到此对象；上述分类不会代替明确failed_phase和恢复提示。

只读可在有界策略内重试；写失败先核对动作账本，效果unknown时禁止盲重试；waiting通过审批决定、用户输入、process.poll或agents.wait推进。取消只停止后续执行，已有效果如实保留。

## 请求示例

示例展示结构；不代表这些示例引用存在。

```json
{
  "workspace_ref": {
    "kind": "workspace",
    "id": "workspace_main",
    "version": "tree_8"
  },
  "change_set_ref": {
    "kind": "changeset",
    "id": "changes_8",
    "version": "1"
  },
  "selected_unit_ids": [
    "unit_main_1"
  ],
  "expected_workspace_version": "tree_8"
}
```

## 成功结构示例

```json
{
  "kind": "ok",
  "payload": {
    "status": "merged",
    "workspace_ref": {
      "kind": "web",
      "id": "example_001",
      "version": "example_001"
    },
    "applied_unit_ids": [],
    "conflict_unit_ids": [],
    "revalidation_required": true
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
| `workspace.changes` | [开发设计](../../../docs/design/components/workspace-changes.md) | `src/uaw/workspace/changes.py` |

[接口机器目录](../../../contracts/interfaces.json) · [统一对象schema](../../../contracts/uaw.schema.json)
