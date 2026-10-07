# file.write

状态：契约0.1，待实现。类别：模型可调用工具。所属：工作区与交付。

写获准根内文件。

[分类索引](../TOOL.md) · [统一规则](../CONVENTIONS.md) · [实际范围](../../implementation/README.md)

## 调用入口

LLM提出 `file.write(arguments)` → ToolRuntime校验/权限/必要审批 → `workspace`负责人。ToolRuntime注入可信上下文，业务参数只使用下方输入结构。

## 输入

[ToolFileWriteInput](../objects/ToolFileWriteInput.md)；每个字段的类型、必填性、默认注解、限制和分支见对象页。

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `workspace_ref` | [Ref](../objects/Ref.md) | 是 | 工作区 |
| `path` | [RelativePath](../objects/RelativePath.md) | 是 | 相对路径 |
| `text` | [Text](../objects/Text.md) | 否 | 新内容 |
| `expected_content_hash` | [Hash](../objects/Hash.md) | 否 | 现有内容摘要 |
| `create_only` | [Bool](../objects/Bool.md) | 是 | 仅新建 |
| `content_ref` | [Ref](../objects/Ref.md) | 否 | 大内容的获准完整blob；与text互斥。 |

## 输出

[ToolFileWriteResult](../objects/ToolFileWriteResult.md) 为完整返回结构。`kind=ok` 的payload是 [ChangeSet](../objects/ChangeSet.md)。`waiting`带wait_ref，其他非成功状态带Failure，不能用空对象假装成功。

| payload字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `id` | [ID](../objects/ID.md) | 是 | 变更集 |
| `base_ref` | [Ref](../objects/Ref.md) | 是 | 基础文件树 |
| `target_ref` | [Ref](../objects/Ref.md) | 是 | 修改后文件树 |
| `units` | 数组&lt;[ChangeUnit](../objects/ChangeUnit.md)&gt; | 是 | 可选择改动 |
| `provenance_refs` | 数组&lt;[Ref](../objects/Ref.md)&gt; | 是 | 命令/模型动作来源 |
| `revision` | [Revision](../objects/Revision.md) | 是 | 登记版本 |

## 约束与提交

- 效果分类：`workspace_write`。
- 认证/上下文：`agent`；范围及权限由服务端或Runner取得。
- 请求/动作ID去重与CAS按[统一规则](../CONVENTIONS.md)执行，重复ID不同参数必须冲突。
- 功能旗标：`file_write`；关闭时发现不展示，直接调用/恢复也拒绝。
- create_only=false须旧摘要；写原子替换、记录before/after；超大内容先上传blob。

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
    "version": "tree_7"
  },
  "path": "src/main.py",
  "text": "print('hello')\n",
  "expected_content_hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "create_only": false
}
```

## 成功结构示例

```json
{
  "kind": "ok",
  "payload": {
    "id": "example_001",
    "base_ref": {
      "kind": "web",
      "id": "example_001",
      "version": "example_001"
    },
    "target_ref": {
      "kind": "web",
      "id": "example_001",
      "version": "example_001"
    },
    "units": [],
    "provenance_refs": [],
    "revision": 0
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
| `workspace.changes` | [开发设计](../../../docs/design/components/workspace-changes.md) | `src/uaw/workspace/changes.py` |

[接口机器目录](../../../contracts/interfaces.json) · [统一对象schema](../../../contracts/uaw.schema.json)
