# 离线质量评测：开发设计

节点 `support.evaluation` · UAW v0.10 · 2026-10-07 · 状态：待实现/待任务验证。

[开发设计索引](../README.md) · [公共契约](../COMMON_CONTRACTS.md) · [关系图谱](../../../ARCHITECTURE_ATLAS.md)

## 职责与代码位置

固定真实任务集、隔离比较版本、人工校准。

- 计划主文件：`src/uaw/shared/evaluation.py`。
- 统一业务入口：`evaluate/compare`；只允许所属 facade 或获准适配器调用。
- 上层归属：`support`。该节点是逻辑组件，不默认独立服务。
- 硬约束：不为每个用户请求执行；防止评测重放外部写入。

## 输入、输出与调用协议

输入请求 `SupportEvaluationRequest` 的领域字段（实验类型，实施时落在所属目录的 contracts.py）：

```text
candidate_manifest: Ref; baseline_manifest: Ref; dataset_version: Ref; fixture_environment: Ref; grader_config: Ref
```

领域输出：切片对比与ReleaseGate。结果使用 `ComponentResult[领域载荷]`；本节点只填实际确认的 `output_refs/revision`，等待、拒绝、冲突、取消和失败均为显式类型。

关联、主体与预算通过 TrustedExecutionContext 注入，不能由模型业务参数覆盖。请求/结果的公共字段与持久化边界见 COMMON_CONTRACTS；传入路径/文字不隐含访问授权。

## 详细处理策略

1. 固定真实输入、初态、权限与工具fixture。
2. 开发/回归/隐藏集分开并查近重复。
3. 隔离跑新旧版本，外部写禁用或模拟。
4. 先真实状态与硬约束，再事实/语义评分和人工校准。
5. 按办公/开发/学术与失败类型报告接受、返工、全成本/延迟。
6. 用证据决定发布门槛，不只看总分。

### 模型参与方式

需要语义判断时，由当前继承模型提出建议；可复用当前主调用或按需发起，不强制专门判断 Agent。技术验证与状态提交仍由代码执行。

## 状态、并发与提交

评测输入、评分器和报告版本不可变；一次运行验收不替代离线系统比较。

同一逻辑请求保持request_id；重试另有attempt_id。持久修改使用预期领域版本/事务或持久执行意图；读取保持实际来源版本。Run事件只引用本节点确认的变化，不能先播成功再尝试提交。

## 失败分支与反馈

- 零接受数成本比不可计算。
- 裁判不确定抽检。
- 被评输出不能改变裁判指令。
- 不完整fixture标不可比。

返回 Failure(code、retryable、failed_phase、recover_hint、evidence_refs)。代码只能恢复明确安全的执行错误；改变用户目标、模型、权限或非等价能力必须回 Agent/用户。

## 缓存、成本与取消

同预算比较单/多Agent；错误样本授权脱敏后回归，禁止真实重复发布。

使用原Run总预算和剩余deadline。取消先停止新动作，再等待执行器实际回执；已经发生的副作用不随文档/聊天回退撤销。引用读取始终复核当前授权/删除。

## 开发验收案例

- 新prompt退步被发现。
- 同模型自评误差人工校准。
- 不能隐藏失败重试成本。

这些是待实现的验收要求，本轮未运行 Runtime 行为测试。首个场景用真实输入/输出/环境建立fixture；权限、版本、取消与副作用用可重复硬检查，语义标准按人工样本校准。

## 逐字段接口与对象定义

[本节点全部接口](../../api/nodes/support.evaluation.md) · [统一对象字典](../../api/OBJECTS.md) · [接口共同规则](../../api/CONVENTIONS.md)

上面的领域字段用于说明策略。准确请求DTO、动作分支、必填性、返回对象和结构规则以接口契约源contracts/interface_catalog.py及其生成schema为准；语义/权限/版本/执行策略仍按本设计落实。出现差异需同时修维护源，不能拿摘要字段替代当前接口校验。

## 模块联系

| 方向 | 关系与载荷 | 对应设计 |
| --- | --- | --- |
| 上游 → 本节点 | 数据/引用：待发布候选 | [扩展包与版本发布](support-extensions.md) |
| 上游 → 本节点 | 数据/引用：授权失败样本 | [运行观测](support-observability.md) |
| 本节点 → 下游 | 权限/配置：回归报告与发布门槛 | [扩展包与版本发布](support-extensions.md) |
| 本节点 → 下游 | 数据/引用：样本与对比版本 | [存储适配与访问](support-stores.md) |

## 参考与需要验证的选择

- [Cache · 在途合并/失效](https://app.notion.com/p/3ec6ccd32c87809fbf70ea46b440a3e3)：参考问题与原则，具体协议为 UAW 自己的设计。
- [Evaluation · 样本/版本/Trace](https://app.notion.com/p/3ec6ccd32c87805596bad437d733ecf9)：参考问题与原则，具体协议为 UAW 自己的设计。

题集是检查遗漏的来源，未逐题验证第三方技术结论。实施阶段涉及具体供应商协议时再核对其官方资料；本文的字段、算法顺序与权限边界不是从题集自动取得的事实。

