# context.retrieval

状态：契约0.1，待实现。类别：细分组件私有接口。所属：上下文与资料。

资料检索与证据的私有阶段输入。

[分类索引](../COMPONENT.md) · [统一规则](../CONVENTIONS.md) · [实际范围](../../implementation/README.md)

## 调用入口

计划Python异步签名：`async def handle(request: InternalContextRetrievalRequest, context: TrustedExecutionContext) -> ComponentContextRetrievalResult`。所属入口为 `context.retrieval`。该签名是契约目标；实际方法定位见对应开发设计，不能从公网/LLM直接调用私有组件。

## 输入

[InternalContextRetrievalRequest](../objects/InternalContextRetrievalRequest.md)；每个字段的类型、必填性、默认注解、限制和分支见对象页。

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `query` | [Text](../objects/Text.md) | 是 | 按当前语义任务生成的检索查询，不使用行业词典固定路由。 |
| `corpus_refs` | 数组&lt;[Ref](../objects/Ref.md)&gt; | 是 | 授权并发布的检索语料；删除资料不可用旧缓存召回。 |
| `active_revisions` | 映射&lt;string, [Revision](../objects/Revision.md)&gt; | 是 | 每个语料当前已发布的索引修订；旧未发布索引不得混入。 |
| `top_k` | integer | 是 | 检索最多命中数，1–64；过滤访问权后再排序。 |
| `freshness` | [FreshnessPolicy](../objects/FreshnessPolicy.md) | 是 | 固定版本、最新必需或政策限定时效。 |
| `max_age_ms` | [Duration](../objects/Duration.md) | 否 | bounded_age必需；0表示不接受陈旧数据。 |

## 输出

[ComponentContextRetrievalResult](../objects/ComponentContextRetrievalResult.md) 为完整返回结构。`kind=ok` 的payload是 [RetrievalPage](../objects/RetrievalPage.md)。`waiting`带wait_ref，其他非成功状态带Failure，不能用空对象假装成功。

| payload字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `items` | 数组&lt;[RetrievalHit](../objects/RetrievalHit.md)&gt; | 是 | 本页 |
| `next_cursor` | [Cursor](../objects/Cursor.md) | 否 | 续页 |
| `snapshot_revision` | [Revision](../objects/Revision.md) | 是 | 读取版本 |

## 约束与提交

- 效果分类：`read`。
- 认证/上下文：`service`；范围及权限由服务端或Runner取得。
- 请求/动作ID去重与CAS按[统一规则](../CONVENTIONS.md)执行，重复ID不同参数必须冲突。
- 保存RetrievalManifest与实际索引版本；不能把高相似排名写成已验证事实。
- 精确引用优先直接读，开放查询才生成检索需求
- 在授权子集中关键词/向量召回而非全库TopK后删
- 合并候选并按目标相关、来源时效/权威与覆盖排序
- 检查证据冲突/缺口，必要时让Agent扩大检索
- 返回前复核当前ACL与实际版本并输出定位引用
- 取消/超时遵从COMMON_CONTRACTS；所有引用必须当前权限内、版本可访问。

## 错误、等待、取消

- 索引不可用返回retrieval_unavailable
- 无命中与读取失败分开
- 撤销候选不能给模型

错误对象是 [Failure](../objects/Failure.md)；统一分类：schema_invalid / permission_denied / feature_disabled / revision_conflict / stale_resource / dependency_unavailable / budget_exceeded / deadline_exceeded / cancelled / unknown_effect。实际Runtime需要把业务错误映射到此对象；上述分类不会代替明确failed_phase和恢复提示。

只读可在有界策略内重试；写失败先核对动作账本，效果unknown时禁止盲重试；waiting通过审批决定、用户输入、process.poll或agents.wait推进。取消只停止后续执行，已有效果如实保留。

## 请求示例

示例展示结构；不代表这些示例引用存在。

```json
{
  "query": "example_001",
  "corpus_refs": [],
  "active_revisions": {},
  "top_k": 1,
  "freshness": "pinned"
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
| `context.retrieval` | [开发设计](../../../docs/design/components/context-retrieval.md) | `src/uaw/context/retrieval.py` |

[接口机器目录](../../../contracts/interfaces.json) · [统一对象schema](../../../contracts/uaw.schema.json)
