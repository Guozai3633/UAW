# context.sources

状态：契约0.1，待实现。类别：细分组件私有接口。所属：上下文与资料。

来源解析的私有阶段输入。

[分类索引](../COMPONENT.md) · [统一规则](../CONVENTIONS.md) · [实际范围](../../implementation/README.md)

## 调用入口

计划Python异步签名：`async def handle(request: InternalContextSourcesRequest, context: TrustedExecutionContext) -> ComponentContextSourcesResult`。所属入口为 `context.sources`。该签名是契约目标；实际方法定位见对应开发设计，不能从公网/LLM直接调用私有组件。

## 输入

[InternalContextSourcesRequest](../objects/InternalContextSourcesRequest.md)；每个字段的类型、必填性、默认注解、限制和分支见对象页。

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `source_refs` | 数组&lt;[Ref](../objects/Ref.md)&gt; | 是 | 实际来源集合，须固定版本、访问权和可定位内容。 |
| `purpose` | [Purpose](../objects/Purpose.md) | 是 | 此次上下文用途，选择相关构建/压缩/裁剪功能。 |
| `source_revision_policy` | enum: `pinned` / `latest_required` | 是 | 允许固定旧版本或要求最新；变化时反馈stale。 |

## 输出

[ComponentContextSourcesResult](../objects/ComponentContextSourcesResult.md) 为完整返回结构。`kind=ok` 的payload是 [SourceBundle](../objects/SourceBundle.md)。`waiting`带wait_ref，其他非成功状态带Failure，不能用空对象假装成功。

| payload字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `source_refs` | 数组&lt;[Ref](../objects/Ref.md)&gt; | 是 | 有效来源 |
| `missing_refs` | 数组&lt;[Ref](../objects/Ref.md)&gt; | 是 | 明确缺口 |
| `manifest` | [Manifest](../objects/Manifest.md) | 是 | 依赖 |

## 约束与提交

- 效果分类：`read`。
- 认证/上下文：`service`；范围及权限由服务端或Runner取得。
- 请求/动作ID去重与CAS按[统一规则](../CONVENTIONS.md)执行，重复ID不同参数必须冲突。
- 只写来源清单，源对象由原领域拥有；latest_required取得版本后也固定本次实际版本。
- 按来源类型分派到History、TaskBoard、Workspace或账号适配器
- 读取前检查scope与当前撤销
- 固定取得的内容版本并核对位置/hash
- 将已知缺失、断开与可用材料分别返回
- 登记SourceManifest供后续检索和引用
- 取消/超时遵从COMMON_CONTRACTS；所有引用必须当前权限内、版本可访问。

## 错误、等待、取消

- 本地断开返回disconnected
- 无权拒绝
- 版本不稳定返回source_changed供重读

错误对象是 [Failure](../objects/Failure.md)；统一分类：schema_invalid / permission_denied / feature_disabled / revision_conflict / stale_resource / dependency_unavailable / budget_exceeded / deadline_exceeded / cancelled / unknown_effect。实际Runtime需要把业务错误映射到此对象；上述分类不会代替明确failed_phase和恢复提示。

只读可在有界策略内重试；写失败先核对动作账本，效果unknown时禁止盲重试；waiting通过审批决定、用户输入、process.poll或agents.wait推进。取消只停止后续执行，已有效果如实保留。

## 请求示例

示例展示结构；不代表这些示例引用存在。

```json
{
  "source_refs": [],
  "purpose": "draft_preview",
  "source_revision_policy": "pinned"
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
| `context.sources` | [开发设计](../../../docs/design/components/context-sources.md) | `src/uaw/context/sources.py` |

[接口机器目录](../../../contracts/interfaces.json) · [统一对象schema](../../../contracts/uaw.schema.json)
