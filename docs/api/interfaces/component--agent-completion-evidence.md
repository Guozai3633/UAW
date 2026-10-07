# agent.completion.evidence

状态：契约0.1，待实现。类别：细分组件私有接口。所属：Agent执行与协作。

真实证据收集的私有阶段输入。

[分类索引](../COMPONENT.md) · [统一规则](../CONVENTIONS.md) · [实际范围](../../implementation/README.md)

## 调用入口

计划Python异步签名：`async def handle(request: InternalAgentCompletionEvidenceRequest, context: TrustedExecutionContext) -> ComponentAgentCompletionEvidenceResult`。所属入口为 `agent.completion.evidence`。该签名是契约目标；实际方法定位见对应开发设计，不能从公网/LLM直接调用私有组件。

## 输入

[InternalAgentCompletionEvidenceRequest](../objects/InternalAgentCompletionEvidenceRequest.md)；每个字段的类型、必填性、默认注解、限制和分支见对象页。

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `contract_ref` | [Ref](../objects/Ref.md) | 是 | 当前目标和验收要求的固定版本。 |
| `artifact_refs` | 数组&lt;[Ref](../objects/Ref.md)&gt; | 是 | 实际存在、获准且固定版本的成果；不接受虚构路径。 |
| `coverage_gaps` | 数组&lt;[ID](../objects/ID.md)&gt; | 是 | 缺乏证据的验收要求ID，用于申请实际检查。 |

## 输出

[ComponentAgentCompletionEvidenceResult](../objects/ComponentAgentCompletionEvidenceResult.md) 为完整返回结构。`kind=ok` 的payload是 [CheckPage](../objects/CheckPage.md)。`waiting`带wait_ref，其他非成功状态带Failure，不能用空对象假装成功。

| payload字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `items` | 数组&lt;[VerificationCheck](../objects/VerificationCheck.md)&gt; | 是 | 本页 |
| `next_cursor` | [Cursor](../objects/Cursor.md) | 否 | 续页 |
| `snapshot_revision` | [Revision](../objects/Revision.md) | 是 | 读取版本 |

## 约束与提交

- 效果分类：`read`。
- 认证/上下文：`service`；范围及权限由服务端或Runner取得。
- 请求/动作ID去重与CAS按[统一规则](../CONVENTIONS.md)执行，重复ID不同参数必须冲突。
- 验证证据是不可变引用，不以模型口述替代。
- 按缺口选择真实读取/测试/计算/格式检查
- 通过Tool请求获准检查与预算
- 登记实际受测版本、环境和输出
- 把passed/failed/not_run/blocked分别返回语义核验
- 取消/超时遵从COMMON_CONTRACTS；所有引用必须当前权限内、版本可访问。

## 错误、等待、取消

- 环境不足标blocked
- 未跑标not_run
- 工具失败不写passed

错误对象是 [Failure](../objects/Failure.md)；统一分类：schema_invalid / permission_denied / feature_disabled / revision_conflict / stale_resource / dependency_unavailable / budget_exceeded / deadline_exceeded / cancelled / unknown_effect。实际Runtime需要把业务错误映射到此对象；上述分类不会代替明确failed_phase和恢复提示。

只读可在有界策略内重试；写失败先核对动作账本，效果unknown时禁止盲重试；waiting通过审批决定、用户输入、process.poll或agents.wait推进。取消只停止后续执行，已有效果如实保留。

## 请求示例

示例展示结构；不代表这些示例引用存在。

```json
{
  "contract_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "artifact_refs": [],
  "coverage_gaps": []
}
```

## 成功结构示例

```json
{
  "kind": "ok",
  "payload": {
    "items": [],
    "snapshot_revision": 0
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
| `agent.completion.evidence` | [开发设计](../../../docs/design/components/agent-completion-evidence.md) | `src/uaw/agent/completion/evidence.py` |

[接口机器目录](../../../contracts/interfaces.json) · [统一对象schema](../../../contracts/uaw.schema.json)
