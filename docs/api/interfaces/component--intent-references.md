# intent.references

状态：契约0.1，待实现。类别：细分组件私有接口。所属：任务理解。

指代解析的私有阶段输入。

[分类索引](../COMPONENT.md) · [统一规则](../CONVENTIONS.md) · [实际范围](../../implementation/README.md)

## 调用入口

计划Python异步签名：`async def handle(request: InternalIntentReferencesRequest, context: TrustedExecutionContext) -> ComponentIntentReferencesResult`。所属入口为 `intent.references`。该签名是契约目标；实际方法定位见对应开发设计，不能从公网/LLM直接调用私有组件。

## 输入

[InternalIntentReferencesRequest](../objects/InternalIntentReferencesRequest.md)；每个字段的类型、必填性、默认注解、限制和分支见对象页。

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `expressions` | 数组&lt;[Text](../objects/Text.md)&gt; | 是 | 用户原文中待消解的指代/文件/材料称呼。 |
| `candidate_scope` | [Scope](../objects/Scope.md) | 是 | 指代消解允许搜索的资源范围。 |
| `expected_versions` | 映射&lt;string, [Revision](../objects/Revision.md)&gt; | 是 | 每个参与资源的预期修订，不允许缺失应校验的资源。 |

## 输出

[ComponentIntentReferencesResult](../objects/ComponentIntentReferencesResult.md) 为完整返回结构。`kind=ok` 的payload是 [SourceBundle](../objects/SourceBundle.md)。`waiting`带wait_ref，其他非成功状态带Failure，不能用空对象假装成功。

| payload字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `source_refs` | 数组&lt;[Ref](../objects/Ref.md)&gt; | 是 | 有效来源 |
| `missing_refs` | 数组&lt;[Ref](../objects/Ref.md)&gt; | 是 | 明确缺口 |
| `manifest` | [Manifest](../objects/Manifest.md) | 是 | 依赖 |

## 约束与提交

- 效果分类：`read`。
- 认证/上下文：`service`；范围及权限由服务端或Runner取得。
- 请求/动作ID去重与CAS按[统一规则](../CONVENTIONS.md)执行，重复ID不同参数必须冲突。
- TaskFrame只记录已解析引用及版本；候选是临时数据，授权由resolver复核。
- 先使用用户明确选中资源和精确ID
- 再查当前会话/项目最近相关引用
- 按语义与位置形成候选并附依据
- 唯一且足够可靠的候选解析为Reference
- 关键动作出现多候选交歧义策略，不凭相似文件名任选
- 取消/超时遵从COMMON_CONTRACTS；所有引用必须当前权限内、版本可访问。

## 错误、等待、取消

- 断开的本地Runner返回source_disconnected
- 多个候选返回ambiguous_reference
- 不可定位返回reference_missing

错误对象是 [Failure](../objects/Failure.md)；统一分类：schema_invalid / permission_denied / feature_disabled / revision_conflict / stale_resource / dependency_unavailable / budget_exceeded / deadline_exceeded / cancelled / unknown_effect。实际Runtime需要把业务错误映射到此对象；上述分类不会代替明确failed_phase和恢复提示。

只读可在有界策略内重试；写失败先核对动作账本，效果unknown时禁止盲重试；waiting通过审批决定、用户输入、process.poll或agents.wait推进。取消只停止后续执行，已有效果如实保留。

## 请求示例

示例展示结构；不代表这些示例引用存在。

```json
{
  "expressions": [],
  "candidate_scope": {
    "principal_id": "example_001"
  },
  "expected_versions": {}
}
```

## 成功结构示例

```json
{
  "kind": "ok",
  "payload": {
    "source_refs": [],
    "missing_refs": [],
    "manifest": {
      "version": "example_001",
      "input_refs": [],
      "dependency_refs": [],
      "content_hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
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
| `intent.references` | [开发设计](../../../docs/design/components/intent-references.md) | `src/uaw/intent/references.py` |

[接口机器目录](../../../contracts/interfaces.json) · [统一对象schema](../../../contracts/uaw.schema.json)
