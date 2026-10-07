# 选择与上下文预算：开发设计

节点 `context.selection` · UAW v0.10 · 2026-10-07 · 状态：待实现/待任务验证。

[开发设计索引](../README.md) · [公共契约](../COMMON_CONTRACTS.md) · [关系图谱](../../../ARCHITECTURE_ATLAS.md)

## 职责与代码位置

按 purpose 选块并预留输出及工具反馈空间。

- 计划主文件：`src/uaw/context/selection.py`。
- 统一业务入口：`select/allocate`；只允许所属 facade 或获准适配器调用。
- 上层归属：`context`。该节点是逻辑组件，不默认独立服务。
- 硬约束：不按固定回合裁剪所有任务。

## 输入、输出与调用协议

输入请求 `ContextSelectionRequest` 的领域字段（实验类型，实施时落在所属目录的 contracts.py）：

```text
candidate_refs: list[Ref]; purpose: Purpose; model_context_limit: int; output_reserve: int; tool_reserve: int
```

领域输出：选中块与分配计划。结果使用 `ComponentResult[领域载荷]`；本节点只填实际确认的 `output_refs/revision`，等待、拒绝、冲突、取消和失败均为显式类型。

关联、主体与预算通过 TrustedExecutionContext 注入，不能由模型业务参数覆盖。请求/结果的公共字段与持久化边界见 COMMON_CONTRACTS；传入路径/文字不隐含访问授权。

## 详细处理策略

1. 先从模型可用窗口扣除输出/工具反馈/必要压缩余量。
2. 用户原文、硬约束与当前未完成状态优先。
3. 按来源可信、目标覆盖、时效、成本选择候选。
4. 大工具结果先分页/筛选，避免用一次压缩解决无限输入。
5. 剩余缺口转压缩或读取需求，不能静默丢关键条件。

### 模型参与方式

需要语义判断时，由当前继承模型提出建议；可复用当前主调用或按需发起，不强制专门判断 Agent。技术验证与状态提交仍由代码执行。

## 状态、并发与提交

记录被选/被排除块和原因到ContextManifest，真实用量更新预算估计。

同一逻辑请求保持request_id；重试另有attempt_id。持久修改使用预期领域版本/事务或持久执行意图；读取保持实际来源版本。Run事件只引用本节点确认的变化，不能先播成功再尝试提交。

## 失败分支与反馈

- 必需内容装不下返回context_insufficient。
- 未知tokenizer使用保守估算并报告。
- 无关块不补满窗口。

返回 Failure(code、retryable、failed_phase、recover_hint、evidence_refs)。代码只能恢复明确安全的执行错误；改变用户目标、模型、权限或非等价能力必须回 Agent/用户。

## 缓存、成本与取消

purpose配置可扩展但不决定固定业务链；保留稳定块身份便于复用。

使用原Run总预算和剩余deadline。取消先停止新动作，再等待执行器实际回执；已经发生的副作用不随文档/聊天回退撤销。引用读取始终复核当前授权/删除。

## 开发验收案例

- 压缩后仍有输出空间。
- 千页返回不会全塞prompt。
- 必需引用不足明确暴露。

这些是待实现的验收要求，本轮未运行 Runtime 行为测试。首个场景用真实输入/输出/环境建立fixture；权限、版本、取消与副作用用可重复硬检查，语义标准按人工样本校准。

## 逐字段接口与对象定义

[本节点全部接口](../../api/nodes/context.selection.md) · [统一对象字典](../../api/OBJECTS.md) · [接口共同规则](../../api/CONVENTIONS.md)

上面的领域字段用于说明策略。准确请求DTO、动作分支、必填性、返回对象和结构规则以接口契约源contracts/interface_catalog.py及其生成schema为准；语义/权限/版本/执行策略仍按本设计落实。出现差异需同时修维护源，不能拿摘要字段替代当前接口校验。

## 模块联系

| 方向 | 关系与载荷 | 对应设计 |
| --- | --- | --- |
| 上游 → 本节点 | 数据/引用：证据候选 | [资料检索与证据](context-retrieval.md) |
| 上游 → 本节点 | 数据/引用：允许读取的记忆 | [记忆生命周期](context-memory.md) |
| 本节点 → 下游 | 调用：需要压缩时 | [压缩与关键项保护](context-compression.md) |
| 本节点 → 下游 | 数据/引用：无需压缩的块 | [装配与快照](context-composer.md) |

## 参考与需要验证的选择

- [Context · 预算/压缩/选择](https://app.notion.com/p/3ec6ccd32c87802fb6c2c7dd51db660d)：参考问题与原则，具体协议为 UAW 自己的设计。
- [Memory · 冲突/删除](https://app.notion.com/p/3ec6ccd32c87803db411c4c48b832941)：参考问题与原则，具体协议为 UAW 自己的设计。
- [RAG · 更新/权限](https://app.notion.com/p/3d66ccd32c87806894a2ec48969c200a)：参考问题与原则，具体协议为 UAW 自己的设计。

题集是检查遗漏的来源，未逐题验证第三方技术结论。实施阶段涉及具体供应商协议时再核对其官方资料；本文的字段、算法顺序与权限边界不是从题集自动取得的事实。

