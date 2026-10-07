# 审批与用户控制：开发设计

节点 `run.approval` · UAW v0.10 · 2026-10-07 · 状态：待实现/待任务验证。

[开发设计索引](../README.md) · [公共契约](../COMMON_CONTRACTS.md) · [关系图谱](../../../ARCHITECTURE_ATLAS.md)

## 职责与代码位置

持久审批、steer/enqueue/replace/cancel/partial。

- 计划主文件：`src/uaw/run/approval.py`。
- 统一业务入口：`control/decide_approval`；只允许所属 facade 或获准适配器调用。
- 上层归属：`run`。该节点是逻辑组件，不默认独立服务。
- 硬约束：assisted/manual/automatic不扩大真实权限。

## 输入、输出与调用协议

输入请求 `RunApprovalRequest` 的领域字段（实验类型，实施时落在所属目录的 contracts.py）：

```text
action_id: ID; arguments_hash: Hash; resource_revision: Version; mode: assisted|manual|automatic; control_mode: steer|enqueue|replace|cancel|deliver_partial?
```

领域输出：ApprovalRef / ControlReceipt。结果使用 `ComponentResult[领域载荷]`；本节点只填实际确认的 `output_refs/revision`，等待、拒绝、冲突、取消和失败均为显式类型。

关联、主体与预算通过 TrustedExecutionContext 注入，不能由模型业务参数覆盖。请求/结果的公共字段与持久化边界见 COMMON_CONTRACTS；传入路径/文字不隐含访问授权。

## 详细处理策略

1. 审批绑定主体、动作/参数、资源、期限和政策。
2. manual等用户，assisted只在预授权范围由独立Reviewer决定，automatic不提示但仍受范围约束。
3. 明确决定持久化并唤醒相关节点。
4. 执行前由Tool/Runner复核当前撤销与变化。
5. steer等控制回执注明生效安全边界和不能取消动作。

### 模型参与方式

本组件的契约和状态处理由代码执行。涉及上游模型内容时把它作为待验证提案或数据，不再自动启动一个决策模型。

## 状态、并发与提交

Run审批是权威，Reviewer不能审批自己，拒绝记录不可被换工具绕过。

同一逻辑请求保持request_id；重试另有attempt_id。持久修改使用预期领域版本/事务或持久执行意图；读取保持实际来源版本。Run事件只引用本节点确认的变化，不能先播成功再尝试提交。

## 失败分支与反馈

- 无回复/超时不批准。
- 参数变化返回approval_stale。
- 代审不确定升级用户。
- 控制版本冲突返回现态。

返回 Failure(code、retryable、failed_phase、recover_hint、evidence_refs)。代码只能恢复明确安全的执行错误；改变用户目标、模型、权限或非等价能力必须回 Agent/用户。

## 缓存、成本与取消

只暂停受影响节点；合并相关用户问题，不能为了减少提示扩大授权。

使用原Run总预算和剩余deadline。取消先停止新动作，再等待执行器实际回执；已经发生的副作用不随文档/聊天回退撤销。引用读取始终复核当前授权/删除。

## 开发验收案例

- 拒绝不执行。
- 批准后目标文件变化重新判断。
- 代审模型继承用户选择。

这些是待实现的验收要求，本轮未运行 Runtime 行为测试。首个场景用真实输入/输出/环境建立fixture；权限、版本、取消与副作用用可重复硬检查，语义标准按人工样本校准。

## 逐字段接口与对象定义

[本节点全部接口](../../api/nodes/run.approval.md) · [统一对象字典](../../api/OBJECTS.md) · [接口共同规则](../../api/CONVENTIONS.md)

上面的领域字段用于说明策略。准确请求DTO、动作分支、必填性、返回对象和结构规则以接口契约源contracts/interface_catalog.py及其生成schema为准；语义/权限/版本/执行策略仍按本设计落实。出现差异需同时修维护源，不能拿摘要字段替代当前接口校验。

## 模块联系

| 方向 | 关系与载荷 | 对应设计 |
| --- | --- | --- |
| 本节点 → 下游 | 状态/事件：干预安全边界 | [Run 与交互项](run-state.md) |
| 本节点 → 下游 | 调用：用户取消 | [取消传播](run-cancel.md) |

## 参考与需要验证的选择

- [Runtime · 预算/deadline/checkpoint](https://app.notion.com/p/3f06ccd32c878070921ce42ff22e6257)：参考问题与原则，具体协议为 UAW 自己的设计。
- [Guardrails · durable审批](https://app.notion.com/p/3f06ccd32c878056b729e7a41fd4232b)：参考问题与原则，具体协议为 UAW 自己的设计。

题集是检查遗漏的来源，未逐题验证第三方技术结论。实施阶段涉及具体供应商协议时再核对其官方资料；本文的字段、算法顺序与权限边界不是从题集自动取得的事实。

