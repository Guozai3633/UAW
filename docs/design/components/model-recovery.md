# 调用恢复：开发设计

节点 `model.recovery` · UAW v0.10 · 2026-10-07 · 状态：待实现/待任务验证。

[开发设计索引](../README.md) · [公共契约](../COMMON_CONTRACTS.md) · [关系图谱](../../../ARCHITECTURE_ATLAS.md)

## 职责与代码位置

超时、限流、协议失败的有限重试。

- 计划主文件：`src/uaw/model/recovery.py`。
- 统一业务入口：`recover`；只允许所属 facade 或获准适配器调用。
- 上层归属：`model`。该节点是逻辑组件，不默认独立服务。
- 硬约束：流式重试不拼接两次输出；固定模型不静默切换。

## 输入、输出与调用协议

输入请求 `ModelRecoveryRequest` 的领域字段（实验类型，实施时落在所属目录的 contracts.py）：

```text
failure: ModelFailure; previous_attempt_ref: Ref; remaining_budget: Budget; retry_policy_ref: Ref
```

领域输出：新attempt或明确失败。结果使用 `ComponentResult[领域载荷]`；本节点只填实际确认的 `output_refs/revision`，等待、拒绝、冲突、取消和失败均为显式类型。

关联、主体与预算通过 TrustedExecutionContext 注入，不能由模型业务参数覆盖。请求/结果的公共字段与持久化边界见 COMMON_CONTRACTS；传入路径/文字不隐含访问授权。

## 详细处理策略

1. 分类限流/网络/协议/参数/取消错误。
2. 同固定模型的瞬时失败有限退避。
3. Auto仅在许可兼容候选内切换。
4. 中途流失败新attempt从确定边界重启，不将两次delta拼接。
5. 记录全部失败费用并按重复无进展停止。

### 模型参与方式

本组件的契约和状态处理由代码执行。涉及上游模型内容时把它作为待验证提案或数据，不再自动启动一个决策模型。

## 状态、并发与提交

新attempt与同一逻辑生成关联；旧输出保留诊断但不能成为有效动作提案。

同一逻辑请求保持request_id；重试另有attempt_id。持久修改使用预期领域版本/事务或持久执行意图；读取保持实际来源版本。Run事件只引用本节点确认的变化，不能先播成功再尝试提交。

## 失败分支与反馈

- 参数错误回Agent/Context修复。
- 固定模型持续失败明确说明。
- 取消不自动重试。

返回 Failure(code、retryable、failed_phase、recover_hint、evidence_refs)。代码只能恢复明确安全的执行错误；改变用户目标、模型、权限或非等价能力必须回 Agent/用户。

## 缓存、成本与取消

传递剩余deadline，退避不能重新取得全预算；切换配置公开记录。

使用原Run总预算和剩余deadline。取消先停止新动作，再等待执行器实际回执；已经发生的副作用不随文档/聊天回退撤销。引用读取始终复核当前授权/删除。

## 开发验收案例

- 同一工具提案不因重试被执行两次。
- 用户固定A无暗换B。
- 失败成本纳入总额。

这些是待实现的验收要求，本轮未运行 Runtime 行为测试。首个场景用真实输入/输出/环境建立fixture；权限、版本、取消与副作用用可重复硬检查，语义标准按人工样本校准。

## 逐字段接口与对象定义

[本节点全部接口](../../api/nodes/model.recovery.md) · [统一对象字典](../../api/OBJECTS.md) · [接口共同规则](../../api/CONVENTIONS.md)

上面的领域字段用于说明策略。准确请求DTO、动作分支、必填性、返回对象和结构规则以接口契约源contracts/interface_catalog.py及其生成schema为准；语义/权限/版本/执行策略仍按本设计落实。出现差异需同时修维护源，不能拿摘要字段替代当前接口校验。

## 模块联系

| 方向 | 关系与载荷 | 对应设计 |
| --- | --- | --- |
| 上游 → 本节点 | 调用：调用失败 | [供应商协议适配](model-adapters.md) |
| 本节点 → 下游 | 调用：有限新尝试 | [调用网关](model-gateway.md) |

## 参考与需要验证的选择

- [Model Strategy · 继承/能力/adapter/usage](https://app.notion.com/p/3ec6ccd32c87807bb032da89a48c45ae)：参考问题与原则，具体协议为 UAW 自己的设计。

题集是检查遗漏的来源，未逐题验证第三方技术结论。实施阶段涉及具体供应商协议时再核对其官方资料；本文的字段、算法顺序与权限边界不是从题集自动取得的事实。

