# 记忆生命周期：开发设计

节点 `context.memory` · UAW v0.10 · 2026-10-07 · 状态：待实现/待任务验证。

[开发设计索引](../README.md) · [公共契约](../COMMON_CONTRACTS.md) · [关系图谱](../../../ARCHITECTURE_ATLAS.md)

## 职责与代码位置

候选、冲突、写入、召回、遗忘与派生删除。

- 计划主文件：`src/uaw/context/memory/facade.py`。
- 统一业务入口：`remember/recall/forget`；只允许所属 facade 或获准适配器调用。
- 上层归属：`context`。该节点是逻辑组件，不默认独立服务。
- 硬约束：用户偏好不能授予权限；未核验结论不升为共享事实。

## 输入、输出与调用协议

输入请求 `ContextMemoryRequest` 的领域字段（实验类型，实施时落在所属目录的 contracts.py）：

```text
candidate: MemoryCandidate?; selector: MemorySelector?; memory_policy_ref: Ref; expected_revision: int?
```

领域输出：Memory revision。结果使用 `ComponentResult[领域载荷]`；本节点只填实际确认的 `output_refs/revision`，等待、拒绝、冲突、取消和失败均为显式类型。

关联、主体与预算通过 TrustedExecutionContext 注入，不能由模型业务参数覆盖。请求/结果的公共字段与持久化边界见 COMMON_CONTRACTS；传入路径/文字不隐含访问授权。

## 详细处理策略

1. 区分显式记住与后台推断候选。
2. 检查读取/贡献开关、用途、作用域和保留期。
3. 按具体槽位/条件查重，用户纠正优先，未决冲突保持待确认。
4. 提交新事实版本后才宣告记住。
5. 召回时复核有效时间和授权。
6. 遗忘立即停止召回并传播到摘要/索引/缓存。

### 模型参与方式

需要语义判断时，由当前继承模型提出建议；可复用当前主调用或按需发起，不强制专门判断 Agent。技术验证与状态提交仍由代码执行。

## 状态、并发与提交

Memory记录source、valid_from/to、supersedes与derived_from，Context是唯一写入者。

同一逻辑请求保持request_id；重试另有attempt_id。持久修改使用预期领域版本/事务或持久执行意图；读取保持实际来源版本。Run事件只引用本节点确认的变化，不能先播成功再尝试提交。

## 失败分支与反馈

- 提交失败如实返回not_saved。
- 低可信研究结论留任务候选。
- 删除部分失败返回待清理项。

返回 Failure(code、retryable、failed_phase、recover_hint、evidence_refs)。代码只能恢复明确安全的执行错误；改变用户目标、模型、权限或非等价能力必须回 Agent/用户。

## 缓存、成本与取消

明确profile槽位可精确读取；仅检索开放经历时使用向量，不每句话写入。

使用原Run总预算和剩余deadline。取消先停止新动作，再等待执行器实际回执；已经发生的副作用不随文档/聊天回退撤销。引用读取始终复核当前授权/删除。

## 开发验收案例

- 记忆关闭不影响当次原文。
- ‘会Go’不等于‘喜欢Go’。
- 删除偏好不从备份悄悄恢复。

这些是待实现的验收要求，本轮未运行 Runtime 行为测试。首个场景用真实输入/输出/环境建立fixture；权限、版本、取消与副作用用可重复硬检查，语义标准按人工样本校准。

## 逐字段接口与对象定义

[本节点全部接口](../../api/nodes/context.memory.md) · [统一对象字典](../../api/OBJECTS.md) · [接口共同规则](../../api/CONVENTIONS.md)

上面的领域字段用于说明策略。准确请求DTO、动作分支、必填性、返回对象和结构规则以接口契约源contracts/interface_catalog.py及其生成schema为准；语义/权限/版本/执行策略仍按本设计落实。出现差异需同时修维护源，不能拿摘要字段替代当前接口校验。

## 内部模块与目录

| 子模块 | 详细开发策略 | 计划代码文件 |
| --- | --- | --- |
| 记忆候选 | [context.memory.candidate](context-memory-candidate.md) | `src/uaw/context/memory/candidate.py` |
| 范围与写入政策 | [context.memory.policy](context-memory-policy.md) | `src/uaw/context/memory/policy.py` |
| 查重与冲突 | [context.memory.conflict](context-memory-conflict.md) | `src/uaw/context/memory/conflict.py` |
| 提交与召回 | [context.memory.store](context-memory-store.md) | `src/uaw/context/memory/store.py` |
| 遗忘与删除传播 | [context.memory.forget](context-memory-forget.md) | `src/uaw/context/memory/forget.py` |

## 模块联系

| 方向 | 关系与载荷 | 对应设计 |
| --- | --- | --- |
| 本节点 → 下游 | 数据/引用：允许读取的记忆 | [选择与上下文预算](context-selection.md) |

## 参考与需要验证的选择

- [Context · 预算/压缩/选择](https://app.notion.com/p/3ec6ccd32c87802fb6c2c7dd51db660d)：参考问题与原则，具体协议为 UAW 自己的设计。
- [Memory · 冲突/删除](https://app.notion.com/p/3ec6ccd32c87803db411c4c48b832941)：参考问题与原则，具体协议为 UAW 自己的设计。
- [RAG · 更新/权限](https://app.notion.com/p/3d66ccd32c87806894a2ec48969c200a)：参考问题与原则，具体协议为 UAW 自己的设计。

题集是检查遗漏的来源，未逐题验证第三方技术结论。实施阶段涉及具体供应商协议时再核对其官方资料；本文的字段、算法顺序与权限边界不是从题集自动取得的事实。

