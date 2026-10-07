# 决策执行 · Agent：模块开发设计

节点 `agent` · UAW v0.10 · 2026-10-07 · 状态：目标设计，Runtime 未实现。

[开发设计索引](../README.md) · [目录设计](../../PROJECT_STRUCTURE.md) · [公共契约](../COMMON_CONTRACTS.md)

## 统一入口与状态所有权

计划包：`src/uaw/agent/`，入口：`src/uaw/agent/facade.py`。

入口契约：`AgentRuntime.define_agent(DefinitionRequest)、start(AgentRequest)、step(StepRequest)、delegate(DelegationRequest)`。

所有权：Agent定义/实例、TaskGraph、TaskBoard、ControlLease和完成协调。

## 内部组织策略

根实例单循环起步，工具发现中同时提供会话Agent摘要。用户持久创建角色用create，实际运行用invoke。语义评估分别决定规划/委派/并发，Scheduler执行硬依赖/资源约束，Join核对子结果，Completion Controller提出真实版本完成提案。

facade接收可信请求并协调子组件；子组件不直接调用其他Runtime的私有实现。只通过注入的port调用邻域公开入口。Python首阶段组合在同一进程内，持久化和本地Runner执行仍通过边界接口。

## 数据与依赖接口

输入：TaskFrame、能力、预算、模型政策。输出：动作提案、NodeResult、CompletionProposal。

注入ports：`ContextFacade、ToolFacade、ModelFacade、RunBudgetPort、WorkspaceFacade、Definition/Instance/Plan/BoardRepository`。

领域类型放本包 contracts.py；模型可见工具schema由Tool消费。Repository不暴露其他模块可任意写本模块对象的方法，修改必须走本模块业务入口。

## 决策、权限与资源策略

决策、角色设计、规划、技能选择和语义核验由继承模型提出；工厂、DAG校验、CAS、控制权与预算由代码落实。

LLM 提议动作，Runtime 检查权限、预算、状态。

每次提交绑定真实版本、当前scope、剩余deadline和预算。固定常规配置与当前撤销分开检查。多模块提交用本地事务或可恢复意图，不能承诺外部动作exactly-once。

## 失败与恢复策略

facade保留失败发生阶段与原始受控引用。参数/依赖/版本冲突回调用者修复；拒绝不通过换工具绕过；副作用unknown先Tool对账。恢复先检查此领域schema/版本兼容，再恢复可继续边界，不用Trace重建权威状态。

## 文件组织规则

- `facade.py`：统一入口、依赖注入、调用编排。
- `contracts.py`：领域请求/结果/版本化对象。
- `ports.py`：存储、跨Runtime与执行器协议。
- 子组件文件/包：实现具体策略，分层节点有自己的facade/contracts/ports。
- `repository.py`：领域存储适配，实现CAS和幂等；业务规则仍在组件。
- `tests/unit/` 与 `tests/integration/`：实现阶段只验证具体风险/门槛，不复制实现。

## 实施与验收门槛

同预算单Agent基线，验证create不启动实例、invoke不污染上下文、父模型继承、子失败与取消传播。

首条真实任务贯通入口/核心子组件；其他节点先保留port，未实现能力不暴露为可调用工具。细分模块策略与验收案例见下面各文档。

## 逐字段接口与对象定义

[本节点全部接口](../../api/nodes/agent.md) · [统一对象字典](../../api/OBJECTS.md) · [接口共同规则](../../api/CONVENTIONS.md)

上面的领域字段用于说明策略。准确请求DTO、动作分支、必填性、返回对象和结构规则以接口契约源contracts/interface_catalog.py及其生成schema为准；语义/权限/版本/执行策略仍按本设计落实。出现差异需同时修维护源，不能拿摘要字段替代当前接口校验。

## 内部模块与目录

| 子模块 | 详细开发策略 | 计划代码文件 |
| --- | --- | --- |
| 子Agent定义与发现 | [agent.definitions](../components/agent-definitions.md) | `src/uaw/agent/definitions/facade.py` |
| Agent 决策循环 | [agent.loop](../components/agent-loop.md) | `src/uaw/agent/loop.py` |
| 按需执行评估 | [agent.assessment](../components/agent-assessment.md) | `src/uaw/agent/assessment.py` |
| 规划与依赖校验 | [agent.planning](../components/agent-planning.md) | `src/uaw/agent/planning.py` |
| 节点与资源调度 | [agent.scheduler](../components/agent-scheduler.md) | `src/uaw/agent/scheduler.py` |
| 委派与控制权 | [agent.collaboration](../components/agent-collaboration.md) | `src/uaw/agent/collaboration/facade.py` |
| 技能与任务模板 | [agent.skills](../components/agent-skills.md) | `src/uaw/agent/skills.py` |
| 完成核验协调 | [agent.completion](../components/agent-completion.md) | `src/uaw/agent/completion/facade.py` |
| 共享任务板 | [agent.board](../components/agent-board.md) | `src/uaw/agent/board.py` |
| 统一实例工厂 | [agent.factory](../components/agent-factory.md) | `src/uaw/agent/factory.py` |

## 模块联系

| 方向 | 关系与载荷 | 对应设计 |
| --- | --- | --- |
| 上游 → 本节点 | 数据/引用：目标、约束、未知项 | [任务理解 · Intent](intent.md) |
| 本节点 → 下游 | 调用：装配本轮输入 | [上下文 · Context](context.md) |
| 本节点 → 下游 | 调用：提出下一步动作 | [模型调用 · Model](model.md) |
| 本节点 → 下游 | 调用：发现/执行动作 | [工具执行 · Tool](tool.md) |
| 上游 → 本节点 | 调用：定义/委派等控制工具 | [工具执行 · Tool](tool.md) |
| 本节点 → 下游 | 调用：隔离分配与交付协调 | [工作区 · Workspace](workspace.md) |
| 上游 → 本节点 | 数据/引用：实际结果/类型化失败 | [工具执行 · Tool](tool.md) |
| 本节点 → 下游 | 状态/事件：预算/检查点/完成申请 | [运行控制 · Run](run.md) |
| 上游 → 本节点 | 权限/配置：技能/能力包与flag | [共享支撑与控制层](support.md) |

## 参考与需要验证的选择

- [Multi-Agent · 角色/路由/委派/上下文](https://app.notion.com/p/3ec6ccd32c8780d6b4f9d357a257bfd9)：参考问题与原则，具体协议为 UAW 自己的设计。
- [Planning · 分解/依赖/修订](https://app.notion.com/p/3ec6ccd32c8780cb836cce28bd809d12)：参考问题与原则，具体协议为 UAW 自己的设计。
- [Skills · 发现/加载/权限](https://app.notion.com/p/3ec6ccd32c87807bb032da89a48c45ae)：参考问题与原则，具体协议为 UAW 自己的设计。

题集是检查遗漏的来源，未逐题验证第三方技术结论。实施阶段涉及具体供应商协议时再核对其官方资料；本文的字段、算法顺序与权限边界不是从题集自动取得的事实。

