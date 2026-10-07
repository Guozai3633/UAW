# context.memory.candidate

状态：契约0.1，待实现。类别：细分组件私有接口。所属：上下文与资料。

记忆候选的私有阶段输入。

[分类索引](../COMPONENT.md) · [统一规则](../CONVENTIONS.md) · [实际范围](../../implementation/README.md)

## 调用入口

计划Python异步签名：`async def handle(request: InternalContextMemoryCandidateRequest, context: TrustedExecutionContext) -> ComponentContextMemoryCandidateResult`。所属入口为 `context.memory.candidate`。该签名是契约目标；实际方法定位见对应开发设计，不能从公网/LLM直接调用私有组件。

## 输入

[InternalContextMemoryCandidateRequest](../objects/InternalContextMemoryCandidateRequest.md)；每个字段的类型、必填性、默认注解、限制和分支见对象页。

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `source_refs` | 数组&lt;[Ref](../objects/Ref.md)&gt; | 是 | 实际来源集合，须固定版本、访问权和可定位内容。 |
| `candidate_kind` | enum: `explicit` / `inferred` | 是 | explicit来源于用户明确要求；inferred先候选后核验。 |
| `content` | [MemoryContent](../objects/MemoryContent.md) | 是 | 有来源且受当前记忆政策约束的内容。 |

## 输出

[ComponentContextMemoryCandidateResult](../objects/ComponentContextMemoryCandidateResult.md) 为完整返回结构。`kind=ok` 的payload是 [MemoryCandidate](../objects/MemoryCandidate.md)。`waiting`带wait_ref，其他非成功状态带Failure，不能用空对象假装成功。

| payload字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `id` | [ID](../objects/ID.md) | 是 | 候选 |
| `content` | [MemoryContent](../objects/MemoryContent.md) | 是 | 候选内容 |
| `origin` | [MemoryOrigin](../objects/MemoryOrigin.md) | 是 | 明确要求或推断 |
| `target_scope` | [ScopeSelector](../objects/ScopeSelector.md) | 是 | 建议范围 |

## 约束与提交

- 效果分类：`read`。
- 认证/上下文：`service`；范围及权限由服务端或Runner取得。
- 请求/动作ID去重与CAS按[统一规则](../CONVENTIONS.md)执行，重复ID不同参数必须冲突。
- 候选未通过之前不进入正式长期召回。
- 识别用户明确记住请求并保留来源
- 普通对话/研究结果只提炼有用途的候选
- 区分偏好、事实、经历与方法
- 推断候选不能先对用户宣告记住
- 取消/超时遵从COMMON_CONTRACTS；所有引用必须当前权限内、版本可访问。

## 错误、等待、取消

- 无来源拒绝持久记忆
- 低稳定内容留任务范围

错误对象是 [Failure](../objects/Failure.md)；统一分类：schema_invalid / permission_denied / feature_disabled / revision_conflict / stale_resource / dependency_unavailable / budget_exceeded / deadline_exceeded / cancelled / unknown_effect。实际Runtime需要把业务错误映射到此对象；上述分类不会代替明确failed_phase和恢复提示。

只读可在有界策略内重试；写失败先核对动作账本，效果unknown时禁止盲重试；waiting通过审批决定、用户输入、process.poll或agents.wait推进。取消只停止后续执行，已有效果如实保留。

## 请求示例

示例展示结构；不代表这些示例引用存在。

```json
{
  "source_refs": [],
  "candidate_kind": "explicit",
  "content": {
    "text": "example_001",
    "kind": "preference",
    "source_refs": []
  }
}
```

## 成功结构示例

```json
{
  "kind": "ok",
  "payload": {
    "id": "example_001",
    "content": {
      "text": "example_001",
      "kind": "preference",
      "source_refs": []
    },
    "origin": "explicit",
    "target_scope": {
      "conversation_id": "example_001"
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
| `context.memory.candidate` | [开发设计](../../../docs/design/components/context-memory-candidate.md) | `src/uaw/context/memory/candidate.py` |

[接口机器目录](../../../contracts/interfaces.json) · [统一对象schema](../../../contracts/uaw.schema.json)
