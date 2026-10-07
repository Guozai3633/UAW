# 摄取与索引发布：开发设计

节点 `context.ingestion` · UAW v0.10 · 2026-10-07 · 状态：待实现/待任务验证。

[开发设计索引](../README.md) · [公共契约](../COMMON_CONTRACTS.md) · [关系图谱](../../../ARCHITECTURE_ATLAS.md)

## 职责与代码位置

解析、切片、索引、发布；增量更新和删除传播。

- 计划主文件：`src/uaw/context/ingestion.py`。
- 统一业务入口：`ingest/publish/delete`；只允许所属 facade 或获准适配器调用。
- 上层归属：`context`。该节点是逻辑组件，不默认独立服务。
- 硬约束：未准备好的新索引不能混入当前有效版本。

## 输入、输出与调用协议

输入请求 `ContextIngestionRequest` 的领域字段（实验类型，实施时落在所属目录的 contracts.py）：

```text
source_ref: Ref; parser_version: Version; chunk_profile: ID; embedding_profile: ID; expected_active_revision: int
```

领域输出：内容块与 active revision。结果使用 `ComponentResult[领域载荷]`；本节点只填实际确认的 `output_refs/revision`，等待、拒绝、冲突、取消和失败均为显式类型。

关联、主体与预算通过 TrustedExecutionContext 注入，不能由模型业务参数覆盖。请求/结果的公共字段与持久化边界见 COMMON_CONTRACTS；传入路径/文字不隐含访问授权。

## 详细处理策略

1. 校验来源可用与解析资源限额。
2. 保留标题/页码/表格结构及定位，产生内容块。
3. 按内容hash避免重复处理并构建关键词/向量派生索引。
4. 验证块完整性、来源与ACL后CAS切换active revision。
5. 删除先让当前访问不可用，再清理块/索引/派生摘要及缓存。

### 模型参与方式

本组件的契约和状态处理由代码执行。涉及上游模型内容时把它作为待验证提案或数据，不再自动启动一个决策模型。

## 状态、并发与提交

新revision构建时不覆盖旧版，发布标记为权威；保留或删除旧内容按用户保留政策。

同一逻辑请求保持request_id；重试另有attempt_id。持久修改使用预期领域版本/事务或持久执行意图；读取保持实际来源版本。Run事件只引用本节点确认的变化，不能先播成功再尝试提交。

## 失败分支与反馈

- 解析失败标parse_failed，不能假称无结果。
- 索引构建失败不发布。
- 并发新版本返回publish_conflict。

返回 Failure(code、retryable、failed_phase、recover_hint、evidence_refs)。代码只能恢复明确安全的执行错误；改变用户目标、模型、权限或非等价能力必须回 Agent/用户。

## 缓存、成本与取消

增量处理改变的块；配置或embedding版本变化仅重建依赖派生内容。

使用原Run总预算和剩余deadline。取消先停止新动作，再等待执行器实际回执；已经发生的副作用不随文档/聊天回退撤销。引用读取始终复核当前授权/删除。

## 开发验收案例

- 新旧索引不会混为一版。
- 大文件解析有资源上限。
- 删除后不能通过摘要再召回。

这些是待实现的验收要求，本轮未运行 Runtime 行为测试。首个场景用真实输入/输出/环境建立fixture；权限、版本、取消与副作用用可重复硬检查，语义标准按人工样本校准。

## 逐字段接口与对象定义

[本节点全部接口](../../api/nodes/context.ingestion.md) · [统一对象字典](../../api/OBJECTS.md) · [接口共同规则](../../api/CONVENTIONS.md)

上面的领域字段用于说明策略。准确请求DTO、动作分支、必填性、返回对象和结构规则以接口契约源contracts/interface_catalog.py及其生成schema为准；语义/权限/版本/执行策略仍按本设计落实。出现差异需同时修维护源，不能拿摘要字段替代当前接口校验。

## 模块联系

| 方向 | 关系与载荷 | 对应设计 |
| --- | --- | --- |
| 上游 → 本节点 | 调用：新增/更新材料 | [来源解析](context-sources.md) |
| 本节点 → 下游 | 数据/引用：已发布索引 | [资料检索与证据](context-retrieval.md) |

## 参考与需要验证的选择

- [Context · 预算/压缩/选择](https://app.notion.com/p/3ec6ccd32c87802fb6c2c7dd51db660d)：参考问题与原则，具体协议为 UAW 自己的设计。
- [Memory · 冲突/删除](https://app.notion.com/p/3ec6ccd32c87803db411c4c48b832941)：参考问题与原则，具体协议为 UAW 自己的设计。
- [RAG · 更新/权限](https://app.notion.com/p/3d66ccd32c87806894a2ec48969c200a)：参考问题与原则，具体协议为 UAW 自己的设计。

题集是检查遗漏的来源，未逐题验证第三方技术结论。实施阶段涉及具体供应商协议时再核对其官方资料；本文的字段、算法顺序与权限边界不是从题集自动取得的事实。

