# context.read

状态：契约0.1，待实现。类别：模型可调用工具。所属：上下文与资料。

读取当前授权资料。

[分类索引](../TOOL.md) · [统一规则](../CONVENTIONS.md) · [实际范围](../../implementation/README.md)

## 调用入口

LLM提出 `context.read(arguments)` → ToolRuntime校验/权限/必要审批 → `context`负责人。ToolRuntime注入可信上下文，业务参数只使用下方输入结构。

## 输入

[ToolContextReadInput](../objects/ToolContextReadInput.md)；每个字段的类型、必填性、默认注解、限制和分支见对象页。

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `references` | 数组&lt;[Ref](../objects/Ref.md)&gt; | 是 | 已知引用 |
| `location` | [Location](../objects/Location.md) | 否 | 位置 |
| `cursor` | [Cursor](../objects/Cursor.md) | 否 | 下一页 |

## 输出

[ToolContextReadResult](../objects/ToolContextReadResult.md) 为完整返回结构。`kind=ok` 的payload是 [ReadResult](../objects/ReadResult.md)。`waiting`带wait_ref，其他非成功状态带Failure，不能用空对象假装成功。

| payload字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `reference_ref` | [Ref](../objects/Ref.md) | 是 | 来源版本 |
| `text` | [Text](../objects/Text.md) | 是 | 片段 |
| `location` | [Location](../objects/Location.md) | 是 | 位置 |
| `next_cursor` | [Cursor](../objects/Cursor.md) | 否 | 下一页 |

## 约束与提交

- 效果分类：`read`。
- 认证/上下文：`agent`；范围及权限由服务端或Runner取得。
- 请求/动作ID去重与CAS按[统一规则](../CONVENTIONS.md)执行，重复ID不同参数必须冲突。


## 错误、等待、取消

错误对象是 [Failure](../objects/Failure.md)；统一分类：schema_invalid / permission_denied / feature_disabled / revision_conflict / stale_resource / dependency_unavailable / budget_exceeded / deadline_exceeded / cancelled / unknown_effect。实际Runtime需要把业务错误映射到此对象；上述分类不会代替明确failed_phase和恢复提示。

只读可在有界策略内重试；写失败先核对动作账本，效果unknown时禁止盲重试；waiting通过审批决定、用户输入、process.poll或agents.wait推进。取消只停止后续执行，已有效果如实保留。

## 请求示例

示例展示结构；不代表这些示例引用存在。

```json
{
  "references": []
}
```

## 成功结构示例

```json
{
  "kind": "ok",
  "payload": {
    "reference_ref": {
      "kind": "web",
      "id": "example_001",
      "version": "example_001"
    },
    "text": "example_001",
    "location": {
      "kind": "whole"
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
| `context.sources` | [开发设计](../../../docs/design/components/context-sources.md) | `src/uaw/context/sources.py` |
| `context.references` | [开发设计](../../../docs/design/components/context-references.md) | `src/uaw/context/references.py` |

[接口机器目录](../../../contracts/interfaces.json) · [统一对象schema](../../../contracts/uaw.schema.json)
