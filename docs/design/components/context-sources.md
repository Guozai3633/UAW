# 来源解析：开发设计

节点 `context.sources` · UAW v0.10 · 2026-10-07 · 状态：待实现/待任务验证。

[开发设计索引](../README.md) · [公共契约](../COMMON_CONTRACTS.md) · [关系图谱](../../../ARCHITECTURE_ATLAS.md)

## 职责与代码位置

读取有权限的原文、文件、Task Board、产物与外部材料。

- 计划主文件：`src/uaw/context/sources.py`。
- 统一业务入口：`resolve_sources`；只允许所属 facade 或获准适配器调用。
- 上层归属：`context`。该节点是逻辑组件，不默认独立服务。
- 硬约束：本地材料走 Workspace 授权适配器。

## 输入、输出与调用协议

输入请求 `ContextSourcesRequest` 的领域字段（实验类型，实施时落在所属目录的 contracts.py）：

```text
source_refs: list[Ref]; purpose: Purpose; source_revision_policy: pinned|latest_required
```

领域输出：SourceManifest。结果使用 `ComponentResult[领域载荷]`；本节点只填实际确认的 `output_refs/revision`，等待、拒绝、冲突、取消和失败均为显式类型。

关联、主体与预算通过 TrustedExecutionContext 注入，不能由模型业务参数覆盖。请求/结果的公共字段与持久化边界见 COMMON_CONTRACTS；传入路径/文字不隐含访问授权。

## 详细处理策略

1. 按来源类型分派到History、TaskBoard、Workspace或账号适配器。
2. 读取前检查scope与当前撤销。
3. 固定取得的内容版本并核对位置/hash。
4. 将已知缺失、断开与可用材料分别返回。
5. 登记SourceManifest供后续检索和引用。

### 模型参与方式

本组件的契约和状态处理由代码执行。涉及上游模型内容时把它作为待验证提案或数据，不再自动启动一个决策模型。

## 状态、并发与提交

只写来源清单，源对象由原领域拥有；latest_required取得版本后也固定本次实际版本。

同一逻辑请求保持request_id；重试另有attempt_id。持久修改使用预期领域版本/事务或持久执行意图；读取保持实际来源版本。Run事件只引用本节点确认的变化，不能先播成功再尝试提交。

## 失败分支与反馈

- 本地断开返回disconnected。
- 无权拒绝。
- 版本不稳定返回source_changed供重读。

返回 Failure(code、retryable、failed_phase、recover_hint、evidence_refs)。代码只能恢复明确安全的执行错误；改变用户目标、模型、权限或非等价能力必须回 Agent/用户。

## 缓存、成本与取消

只读必要片段；缓存键包含来源版本/可见域，临时下载链接不持久当源。

使用原Run总预算和剩余deadline。取消先停止新动作，再等待执行器实际回执；已经发生的副作用不随文档/聊天回退撤销。引用读取始终复核当前授权/删除。

## 开发验收案例

- 网页摘要与正文区分。
- 当前版本变化可以发现。
- 断开不伪装文件为空。

这些是待实现的验收要求，本轮未运行 Runtime 行为测试。首个场景用真实输入/输出/环境建立fixture；权限、版本、取消与副作用用可重复硬检查，语义标准按人工样本校准。

## 逐字段接口与对象定义

[本节点全部接口](../../api/nodes/context.sources.md) · [统一对象字典](../../api/OBJECTS.md) · [接口共同规则](../../api/CONVENTIONS.md)

上面的领域字段用于说明策略。准确请求DTO、动作分支、必填性、返回对象和结构规则以接口契约源contracts/interface_catalog.py及其生成schema为准；语义/权限/版本/执行策略仍按本设计落实。出现差异需同时修维护源，不能拿摘要字段替代当前接口校验。

## 模块联系

| 方向 | 关系与载荷 | 对应设计 |
| --- | --- | --- |
| 本节点 → 下游 | 调用：新增/更新材料 | [摄取与索引发布](context-ingestion.md) |
| 本节点 → 下游 | 调用：明确来源或查询 | [资料检索与证据](context-retrieval.md) |
| 本节点 → 下游 | 调用：登记来源 | [引用登记与解析](context-references.md) |

## 参考与需要验证的选择

- [Context · 预算/压缩/选择](https://app.notion.com/p/3ec6ccd32c87802fb6c2c7dd51db660d)：参考问题与原则，具体协议为 UAW 自己的设计。
- [Memory · 冲突/删除](https://app.notion.com/p/3ec6ccd32c87803db411c4c48b832941)：参考问题与原则，具体协议为 UAW 自己的设计。
- [RAG · 更新/权限](https://app.notion.com/p/3d66ccd32c87806894a2ec48969c200a)：参考问题与原则，具体协议为 UAW 自己的设计。

题集是检查遗漏的来源，未逐题验证第三方技术结论。实施阶段涉及具体供应商协议时再核对其官方资料；本文的字段、算法顺序与权限边界不是从题集自动取得的事实。

