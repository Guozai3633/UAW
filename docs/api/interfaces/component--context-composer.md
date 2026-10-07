# context.composer

状态：契约0.1，待实现。类别：细分组件私有接口。所属：上下文与资料。

装配与快照的私有阶段输入。

[分类索引](../COMPONENT.md) · [统一规则](../CONVENTIONS.md) · [实际范围](../../implementation/README.md)

## 调用入口

计划Python异步签名：`async def handle(request: InternalContextComposerRequest, context: TrustedExecutionContext) -> ComponentContextComposerResult`。所属入口为 `context.composer`。该签名是契约目标；实际方法定位见对应开发设计，不能从公网/LLM直接调用私有组件。

## 输入

[InternalContextComposerRequest](../objects/InternalContextComposerRequest.md)；每个字段的类型、必填性、默认注解、限制和分支见对象页。

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `instruction_set_ref` | [Ref](../objects/Ref.md) | 是 | 按来源优先级和作用域解决的指令集合。 |
| `selected_block_refs` | 数组&lt;[Ref](../objects/Ref.md)&gt; | 是 | 经过预算分配、来源/权限核对的上下文块。 |
| `capability_snapshot` | [Ref](../objects/Ref.md) | 是 | 当前有效能力及旗标版本，用于缩小候选。 |
| `context_epoch` | [Revision](../objects/Revision.md) | 是 | 上下文纪元，旧快照不能向新纪元追加。 |

## 输出

[ComponentContextComposerResult](../objects/ComponentContextComposerResult.md) 为完整返回结构。`kind=ok` 的payload是 [ContextSnapshot](../objects/ContextSnapshot.md)。`waiting`带wait_ref，其他非成功状态带Failure，不能用空对象假装成功。

| payload字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `id` | [ID](../objects/ID.md) | 是 | 快照 |
| `epoch` | [Revision](../objects/Revision.md) | 是 | 上下文纪元 |
| `purpose` | [Purpose](../objects/Purpose.md) | 是 | 构建目的 |
| `blocks` | 数组&lt;[ContextBlock](../objects/ContextBlock.md)&gt; | 是 | 按顺序输入 |
| `instruction_set_ref` | [Ref](../objects/Ref.md) | 是 | 已解决规则 |
| `capability_snapshot_ref` | [Ref](../objects/Ref.md) | 是 | 本轮工具/角色摘要 |
| `manifest` | [Manifest](../objects/Manifest.md) | 是 | 依赖 |
| `input_tokens` | [Count](../objects/Count.md) | 是 | 估算输入量 |
| `output_reserve` | [Count](../objects/Count.md) | 是 | 保留输出Token |
| `tool_reserve` | [Count](../objects/Count.md) | 是 | 保留工具往返Token |
| `omitted_refs` | 数组&lt;[Ref](../objects/Ref.md)&gt; | 是 | 主动裁剪资料 |
| `compressed_refs` | 数组&lt;[Ref](../objects/Ref.md)&gt; | 是 | 语义压缩结果 |

## 约束与提交

- 效果分类：`read`。
- 认证/上下文：`service`；范围及权限由服务端或Runner取得。
- 请求/动作ID去重与CAS按[统一规则](../CONVENTIONS.md)执行，重复ID不同参数必须冲突。
- 快照内容不可变；装配源引用保留以便诊断，删除/撤销可使其不可再读取。
- 按可信指令、角色方法、用户原文、必要历史、实时材料分区
- 稳定共同前缀与schema规范序列化
- 实际可用工具与会话Agent摘要按权限装配
- 数据块标来源但不提升信任权限
- 核对预算与依赖版本后返回ContextSnapshot及Manifest
- 取消/超时遵从COMMON_CONTRACTS；所有引用必须当前权限内、版本可访问。

## 错误、等待、取消

- 依赖stale重新选择块
- 缺角色必需方法返回dependency_missing
- 序列化超预算不发模型

错误对象是 [Failure](../objects/Failure.md)；统一分类：schema_invalid / permission_denied / feature_disabled / revision_conflict / stale_resource / dependency_unavailable / budget_exceeded / deadline_exceeded / cancelled / unknown_effect。实际Runtime需要把业务错误映射到此对象；上述分类不会代替明确failed_phase和恢复提示。

只读可在有界策略内重试；写失败先核对动作账本，效果unknown时禁止盲重试；waiting通过审批决定、用户输入、process.poll或agents.wait推进。取消只停止后续执行，已有效果如实保留。

## 请求示例

示例展示结构；不代表这些示例引用存在。

```json
{
  "instruction_set_ref": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "selected_block_refs": [],
  "capability_snapshot": {
    "kind": "web",
    "id": "example_001",
    "version": "example_001"
  },
  "context_epoch": 0
}
```

## 成功结构示例

```json
{
  "kind": "ok",
  "payload": {
    "id": "example_001",
    "epoch": 0,
    "purpose": "draft_preview",
    "blocks": [],
    "instruction_set_ref": {
      "kind": "web",
      "id": "example_001",
      "version": "example_001"
    },
    "capability_snapshot_ref": {
      "kind": "web",
      "id": "example_001",
      "version": "example_001"
    },
    "manifest": {
      "version": "example_001",
      "input_refs": [],
      "dependency_refs": [],
      "content_hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    },
    "input_tokens": 0,
    "output_reserve": 0,
    "tool_reserve": 0,
    "omitted_refs": [],
    "compressed_refs": []
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
| `context.composer` | [开发设计](../../../docs/design/components/context-composer.md) | `src/uaw/context/composer.py` |

[接口机器目录](../../../contracts/interfaces.json) · [统一对象schema](../../../contracts/uaw.schema.json)
