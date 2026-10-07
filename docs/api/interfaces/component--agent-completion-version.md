# agent.completion.version

状态：契约0.1，待实现。类别：细分组件私有接口。所属：Agent执行与协作。

版本与硬条件校验的私有阶段输入。

[分类索引](../COMPONENT.md) · [统一规则](../CONVENTIONS.md) · [实际范围](../../implementation/README.md)

## 调用入口

计划Python异步签名：`async def handle(request: InternalAgentCompletionVersionRequest, context: TrustedExecutionContext) -> ComponentAgentCompletionVersionResult`。所属入口为 `agent.completion.version`。该签名是契约目标；实际方法定位见对应开发设计，不能从公网/LLM直接调用私有组件。

## 输入

[InternalAgentCompletionVersionRequest](../objects/InternalAgentCompletionVersionRequest.md)；每个字段的类型、必填性、默认注解、限制和分支见对象页。

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `report_ref` | [Ref](../objects/Ref.md) | 是 | 绑定当前成果版本的真实核验报告。 |
| `expected_artifact_versions` | 映射&lt;string, [Version](../objects/Version.md)&gt; | 是 | 待完成成果的实际版本；内容变化使旧验证失效。 |
| `pending_effect_refs` | 数组&lt;[Ref](../objects/Ref.md)&gt; | 是 | 完成提交时尚未知的外部效果，阻止虚假成功。 |

## 输出

[ComponentAgentCompletionVersionResult](../objects/ComponentAgentCompletionVersionResult.md) 为完整返回结构。`kind=ok` 的payload是 [ValidationReport](../objects/ValidationReport.md)。`waiting`带wait_ref，其他非成功状态带Failure，不能用空对象假装成功。

| payload字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `valid` | [Bool](../objects/Bool.md) | 是 | 是否通过 |
| `normalized_ref` | [Ref](../objects/Ref.md) | 否 | 规范化对象 |
| `violations` | 数组&lt;[ValidationIssue](../objects/ValidationIssue.md)&gt; | 是 | 问题 |
| `evidence_refs` | 数组&lt;[Ref](../objects/Ref.md)&gt; | 是 | 依据 |

## 约束与提交

- 效果分类：`read`。
- 认证/上下文：`service`；范围及权限由服务端或Runner取得。
- 请求/动作ID去重与CAS按[统一规则](../CONVENTIONS.md)执行，重复ID不同参数必须冲突。
- 提案绑定当前revision，最终CAS归Run。
- 读取真实成果/环境/目标版本
- 按报告依赖比较实际受测输入
- 核对必需检查、权限和未决效果
- 通过才给可提交提案，stale项计算重验范围
- 取消/超时遵从COMMON_CONTRACTS；所有引用必须当前权限内、版本可访问。

## 错误、等待、取消

- 版本改变返回stale_verification
- 必需未知效果阻止succeeded

错误对象是 [Failure](../objects/Failure.md)；统一分类：schema_invalid / permission_denied / feature_disabled / revision_conflict / stale_resource / dependency_unavailable / budget_exceeded / deadline_exceeded / cancelled / unknown_effect。实际Runtime需要把业务错误映射到此对象；上述分类不会代替明确failed_phase和恢复提示。

只读可在有界策略内重试；写失败先核对动作账本，效果unknown时禁止盲重试；waiting通过审批决定、用户输入、process.poll或agents.wait推进。取消只停止后续执行，已有效果如实保留。

## 请求示例

示例展示结构；不代表这些示例引用存在。

```json
{
  "report_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "expected_artifact_versions": {},
  "pending_effect_refs": []
}
```

## 成功结构示例

```json
{
  "kind": "ok",
  "payload": {
    "valid": true,
    "violations": [],
    "evidence_refs": []
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
| `agent.completion.version` | [开发设计](../../../docs/design/components/agent-completion-version.md) | `src/uaw/agent/completion/version.py` |

[接口机器目录](../../../contracts/interfaces.json) · [统一对象schema](../../../contracts/uaw.schema.json)
