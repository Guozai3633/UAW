# Agent 决策循环：开发设计

节点 `agent.loop` · UAW v0.10 · 2026-10-07 · 状态：待实现/待任务验证。

[开发设计索引](../README.md) · [公共契约](../COMMON_CONTRACTS.md) · [关系图谱](../../../ARCHITECTURE_ATLAS.md)

## 职责与代码位置

上下文→模型→动作→观察，主 Agent 保持精炼指令。

- 计划主文件：`src/uaw/agent/loop.py`。
- 统一业务入口：`step`；只允许所属 facade 或获准适配器调用。
- 上层归属：`agent`。该节点是逻辑组件，不默认独立服务。
- 硬约束：失败回到决策，不强制固定业务流水线。

## 输入、输出与调用协议

输入请求 `AgentLoopRequest` 的领域字段（实验类型，实施时落在所属目录的 contracts.py）：

```text
instance_ref: Ref; observations: list[Ref]; current_frame_ref: Ref; remaining_budget: Budget
```

领域输出：动作提案或答复。结果使用 `ComponentResult[领域载荷]`；本节点只填实际确认的 `output_refs/revision`，等待、拒绝、冲突、取消和失败均为显式类型。

关联、主体与预算通过 TrustedExecutionContext 注入，不能由模型业务参数覆盖。请求/结果的公共字段与持久化边界见 COMMON_CONTRACTS；传入路径/文字不隐含访问授权。

## 详细处理策略

1. 读取当前用户修订与实例状态。
2. Context按agent_step装配实际可用定义/工具摘要。
3. 当前继承模型提出答复、发现、调用、规划或委派。
4. 对动作进行生命周期/预算检查，工具动作统一交Tool。
5. 消费实际ToolResult或子结果而非模拟成功文本。
6. 有新约束先失效受影响状态，再决定下一步或申请完成。

### 模型参与方式

需要语义判断时，由当前继承模型提出建议；可复用当前主调用或按需发起，不强制专门判断 Agent。技术验证与状态提交仍由代码执行。

## 状态、并发与提交

每个实例只提交自己的版本化状态；关键观察引用保留，Run存checkpoint引用。

同一逻辑请求保持request_id；重试另有attempt_id。持久修改使用预期领域版本/事务或持久执行意图；读取保持实际来源版本。Run事件只引用本节点确认的变化，不能先播成功再尝试提交。

## 失败分支与反馈

- 模型协议错误交Model恢复。
- 工具错误消费类型结果。
- 重复无进展或额度耗尽交付部分/询问，不无限循环。

返回 Failure(code、retryable、failed_phase、recover_hint、evidence_refs)。代码只能恢复明确安全的执行错误；改变用户目标、模型、权限或非等价能力必须回 Agent/用户。

## 缓存、成本与取消

按需取上下文，不每轮重复完整角色定义；决定与结果分离计量。

使用原Run总预算和剩余deadline。取消先停止新动作，再等待执行器实际回执；已经发生的副作用不随文档/聊天回退撤销。引用读取始终复核当前授权/删除。

## 开发验收案例

- 单次问答不生成DAG。
- 工具失败不会被跳过。
- steer在安全边界影响下一动作。

这些是待实现的验收要求，本轮未运行 Runtime 行为测试。首个场景用真实输入/输出/环境建立fixture；权限、版本、取消与副作用用可重复硬检查，语义标准按人工样本校准。

## 逐字段接口与对象定义

[本节点全部接口](../../api/nodes/agent.loop.md) · [统一对象字典](../../api/OBJECTS.md) · [接口共同规则](../../api/CONVENTIONS.md)

上面的领域字段用于说明策略。准确请求DTO、动作分支、必填性、返回对象和结构规则以接口契约源contracts/interface_catalog.py及其生成schema为准；语义/权限/版本/执行策略仍按本设计落实。出现差异需同时修维护源，不能拿摘要字段替代当前接口校验。

## 模块联系

| 方向 | 关系与载荷 | 对应设计 |
| --- | --- | --- |
| 上游 → 本节点 | 数据/引用：按需方法 | [技能与任务模板](agent-skills.md) |
| 本节点 → 下游 | 调用：不确定执行方式时 | [按需执行评估](agent-assessment.md) |
| 本节点 → 下游 | 调用：提出交付时 | [完成核验协调](agent-completion.md) |
| 上游 → 本节点 | 数据/引用：缺口与补救 | [完成核验协调](agent-completion.md) |
| 上游 → 本节点 | 调用：执行节点 | [节点与资源调度](agent-scheduler.md) |
| 上游 → 本节点 | 生命周期：固定定义后的实例运行 | [统一实例工厂](agent-factory.md) |
| 上游 → 本节点 | 数据/引用：Context提供会话候选，非自动调用 | [子Agent定义与发现](agent-definitions.md) |

## 参考与需要验证的选择

- [Multi-Agent · 角色/路由/委派/上下文](https://app.notion.com/p/3ec6ccd32c8780d6b4f9d357a257bfd9)：参考问题与原则，具体协议为 UAW 自己的设计。
- [Planning · 分解/依赖/修订](https://app.notion.com/p/3ec6ccd32c8780cb836cce28bd809d12)：参考问题与原则，具体协议为 UAW 自己的设计。
- [Skills · 发现/加载/权限](https://app.notion.com/p/3ec6ccd32c87807bb032da89a48c45ae)：参考问题与原则，具体协议为 UAW 自己的设计。

题集是检查遗漏的来源，未逐题验证第三方技术结论。实施阶段涉及具体供应商协议时再核对其官方资料；本文的字段、算法顺序与权限边界不是从题集自动取得的事实。

