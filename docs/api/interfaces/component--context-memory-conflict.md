# context.memory.conflict

状态：契约0.1，待实现。类别：细分组件私有接口。所属：上下文与资料。

查重与冲突的私有阶段输入。

[分类索引](../COMPONENT.md) · [统一规则](../CONVENTIONS.md) · [实际范围](../../implementation/README.md)

## 调用入口

计划Python异步签名：`async def handle(request: InternalContextMemoryConflictRequest, context: TrustedExecutionContext) -> ComponentContextMemoryConflictResult`。所属入口为 `context.memory.conflict`。该签名是契约目标；实际方法定位见对应开发设计，不能从公网/LLM直接调用私有组件。

## 输入

[InternalContextMemoryConflictRequest](../objects/InternalContextMemoryConflictRequest.md)；每个字段的类型、必填性、默认注解、限制和分支见对象页。

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `candidate_ref` | [Ref](../objects/Ref.md) | 是 | 尚未确认的记忆/结果候选版本。 |
| `existing_refs` | 数组&lt;[Ref](../objects/Ref.md)&gt; | 是 | 同作用域的已有记忆版本，用于语义冲突核对。 |
| `slot_key` | [Text](../objects/Text.md) | 否 | 同主题互斥事实/偏好的逻辑位置。 |
| `expected_revision` | [Revision](../objects/Revision.md) | 是 | 目标域CAS版本；不匹配返回conflict并重新读取。 |

## 输出

[ComponentContextMemoryConflictResult](../objects/ComponentContextMemoryConflictResult.md) 为完整返回结构。`kind=ok` 的payload是 [MemoryConflictDecision](../objects/MemoryConflictDecision.md)。`waiting`带wait_ref，其他非成功状态带Failure，不能用空对象假装成功。

| payload字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `action` | [MemoryConflictAction](../objects/MemoryConflictAction.md) | 是 | 新增/更新/澄清/拒绝 |
| `candidate_ref` | [Ref](../objects/Ref.md) | 是 | 候选 |
| `conflicting_refs` | 数组&lt;[Ref](../objects/Ref.md)&gt; | 是 | 冲突 |
| `reason` | [NonEmptyText](../objects/NonEmptyText.md) | 是 | 依据 |

## 约束与提交

- 效果分类：`read`。
- 认证/上下文：`service`；范围及权限由服务端或Runner取得。
- 请求/动作ID去重与CAS按[统一规则](../CONVENTIONS.md)执行，重复ID不同参数必须冲突。
- 不原地抹掉来源历史，提交新的事实版本。
- 先按精确槽位和有效条件查重
- 再用语义寻找可能冲突
- 用户明确纠正优先并生成supersedes
- 不同条件都成立分开保存，无法确定保留候选待确认
- 取消/超时遵从COMMON_CONTRACTS；所有引用必须当前权限内、版本可访问。

## 错误、等待、取消

- 并发纠正CAS冲突重读
- 相似而非相同不得合并

错误对象是 [Failure](../objects/Failure.md)；统一分类：schema_invalid / permission_denied / feature_disabled / revision_conflict / stale_resource / dependency_unavailable / budget_exceeded / deadline_exceeded / cancelled / unknown_effect。实际Runtime需要把业务错误映射到此对象；上述分类不会代替明确failed_phase和恢复提示。

只读可在有界策略内重试；写失败先核对动作账本，效果unknown时禁止盲重试；waiting通过审批决定、用户输入、process.poll或agents.wait推进。取消只停止后续执行，已有效果如实保留。

## 请求示例

示例展示结构；不代表这些示例引用存在。

```json
{
  "candidate_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "existing_refs": [],
  "expected_revision": 0
}
```

## 成功结构示例

```json
{
  "kind": "ok",
  "payload": {
    "action": "insert",
    "candidate_ref": {
      "kind": "web",
      "id": "example_001",
      "version": "example_001"
    },
    "conflicting_refs": [],
    "reason": "example_001"
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
| `context.memory.conflict` | [开发设计](../../../docs/design/components/context-memory-conflict.md) | `src/uaw/context/memory/conflict.py` |

[接口机器目录](../../../contracts/interfaces.json) · [统一对象schema](../../../contracts/uaw.schema.json)
