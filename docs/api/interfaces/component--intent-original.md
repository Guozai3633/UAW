# intent.original

状态：契约0.1，待实现。类别：细分组件私有接口。所属：任务理解。

原文读取的私有阶段输入。

[分类索引](../COMPONENT.md) · [统一规则](../CONVENTIONS.md) · [实际范围](../../implementation/README.md)

## 调用入口

计划Python异步签名：`async def handle(request: InternalIntentOriginalRequest, context: TrustedExecutionContext) -> ComponentIntentOriginalResult`。所属入口为 `intent.original`。该签名是契约目标；实际方法定位见对应开发设计，不能从公网/LLM直接调用私有组件。

## 输入

[InternalIntentOriginalRequest](../objects/InternalIntentOriginalRequest.md)；每个字段的类型、必填性、默认注解、限制和分支见对象页。

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `original_input_ref` | [UserInputRef](../objects/UserInputRef.md) | 是 | 获准且不可变的原始用户输入；不得指向模型摘要。 |
| `user_patch_refs` | 数组&lt;[Ref](../objects/Ref.md)&gt; | 是 | 运行中追加的用户要求版本，原文不覆盖。 |

## 输出

[ComponentIntentOriginalResult](../objects/ComponentIntentOriginalResult.md) 为完整返回结构。`kind=ok` 的payload是 [InputRecord](../objects/InputRecord.md)。`waiting`带wait_ref，其他非成功状态带Failure，不能用空对象假装成功。

| payload字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `id` | [ID](../objects/ID.md) | 是 | 输入 |
| `conversation_id` | [ID](../objects/ID.md) | 是 | 会话 |
| `turn_id` | [ID](../objects/ID.md) | 是 | 轮次 |
| `text` | [Text](../objects/Text.md) | 是 | 用户原文 |
| `attachment_refs` | 数组&lt;[Ref](../objects/Ref.md)&gt; | 是 | 获准附件 |
| `created_at` | [Timestamp](../objects/Timestamp.md) | 是 | 提交时间 |

## 约束与提交

- 效果分类：`read`。
- 认证/上下文：`service`；范围及权限由服务端或Runner取得。
- 请求/动作ID去重与CAS按[统一规则](../CONVENTIONS.md)执行，重复ID不同参数必须冲突。
- 只读原文，不维护第二份可修改账本；纠正必须先成为新的用户输入记录。
- 向Run History读取原始用户输入及明确修订
- 校验作用域、内容版本和资源可访问性
- 保留原文顺序和每项来源
- 返回只读输入集给语义解析，不将AI预览混入用户指令
- 取消/超时遵从COMMON_CONTRACTS；所有引用必须当前权限内、版本可访问。

## 错误、等待、取消

- 缺失引用返回input_missing
- 版本不匹配回取权威记录
- 已删除资料返回不可用状态

错误对象是 [Failure](../objects/Failure.md)；统一分类：schema_invalid / permission_denied / feature_disabled / revision_conflict / stale_resource / dependency_unavailable / budget_exceeded / deadline_exceeded / cancelled / unknown_effect。实际Runtime需要把业务错误映射到此对象；上述分类不会代替明确failed_phase和恢复提示。

只读可在有界策略内重试；写失败先核对动作账本，效果unknown时禁止盲重试；waiting通过审批决定、用户输入、process.poll或agents.wait推进。取消只停止后续执行，已有效果如实保留。

## 请求示例

示例展示结构；不代表这些示例引用存在。

```json
{
  "original_input_ref": {
    "kind": "input",
    "id": "example_001",
    "version": "example_001"
  },
  "user_patch_refs": []
}
```

## 成功结构示例

```json
{
  "kind": "ok",
  "payload": {
    "id": "example_001",
    "conversation_id": "example_001",
    "turn_id": "example_001",
    "text": "example_001",
    "attachment_refs": [],
    "created_at": "2026-10-07T02:00:00Z"
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
| `intent.original` | [开发设计](../../../docs/design/components/intent-original.md) | `src/uaw/intent/original.py` |

[接口机器目录](../../../contracts/interfaces.json) · [统一对象schema](../../../contracts/uaw.schema.json)
