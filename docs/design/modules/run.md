# 运行控制 · Run：模块开发设计

节点 `run` · UAW v0.10 · 2026-10-07 · 状态：目标设计，Runtime 未实现。

[开发设计索引](../README.md) · [目录设计](../../PROJECT_STRUCTURE.md) · [公共契约](../COMMON_CONTRACTS.md)

## 统一入口与状态所有权

计划包：`src/uaw/run/`，入口：`src/uaw/run/facade.py`。

入口契约：`RunRuntime.create(RunRequest)、control(ControlRequest)、decide_approval(ApprovalDecision)、checkpoint/resume(RecoveryRequest)`。

所有权：不可变用户输入/历史、RunState、Items/Event、BudgetLedger、审批/控制与checkpoint/lease。

## 内部组织策略

受理保存原文与轻量Run，关键变化追加Item/Event。预算预留/结算共享总额，用户控制安全边界注入。checkpoint引用领域版本；恢复租约→兼容→当前访问→Tool效果对账→Workspace版本→继续。取消聚合真实执行器回执。

facade接收可信请求并协调子组件；子组件不直接调用其他Runtime的私有实现。只通过注入的port调用邻域公开入口。Python首阶段组合在同一进程内，持久化和本地Runner执行仍通过边界接口。

## 数据与依赖接口

输入：执行请求、版本、用户控制。输出：RunState、Items、事件、checkpoint。

注入ports：`History/Run/Event/Budget/Approval/CheckpointRepository、Agent/Tool/Workspace控制接口、ConfigurationReader、EventTransport`。

领域类型放本包 contracts.py；模型可见工具schema由Tool消费。Repository不暴露其他模块可任意写本模块对象的方法，修改必须走本模块业务入口。

## 决策、权限与资源策略

状态机、账本、恢复、取消与事件都由代码。assisted代审调用独立Reviewer且继承模型，决定只在预授权范围有效。

完成文本不证明成功，completed 与 succeeded 分开。

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

重复受理、事件重连、双预算预留、拒绝/撤销、崩溃恢复及completed与succeeded分开。

首条真实任务贯通入口/核心子组件；其他节点先保留port，未实现能力不暴露为可调用工具。细分模块策略与验收案例见下面各文档。

## 逐字段接口与对象定义

[本节点全部接口](../../api/nodes/run.md) · [统一对象字典](../../api/OBJECTS.md) · [接口共同规则](../../api/CONVENTIONS.md)

上面的领域字段用于说明策略。准确请求DTO、动作分支、必填性、返回对象和结构规则以接口契约源contracts/interface_catalog.py及其生成schema为准；语义/权限/版本/执行策略仍按本设计落实。出现差异需同时修维护源，不能拿摘要字段替代当前接口校验。

## 内部模块与目录

| 子模块 | 详细开发策略 | 计划代码文件 |
| --- | --- | --- |
| 历史与输入权威 | [run.history](../components/run-history.md) | `src/uaw/run/history.py` |
| Run 与交互项 | [run.state](../components/run-state.md) | `src/uaw/run/state.py` |
| 事件与重连 | [run.events](../components/run-events.md) | `src/uaw/run/events.py` |
| 预算与准入 | [run.budget](../components/run-budget.md) | `src/uaw/run/budget.py` |
| 审批与用户控制 | [run.approval](../components/run-approval.md) | `src/uaw/run/approval.py` |
| 恢复边界与版本 | [run.checkpoint](../components/run-checkpoint.md) | `src/uaw/run/checkpoint.py` |
| 租约与执行恢复 | [run.resume](../components/run-resume.md) | `src/uaw/run/resume/facade.py` |
| 取消传播 | [run.cancel](../components/run-cancel.md) | `src/uaw/run/cancel.py` |
| 未来触发器 | [run.trigger](../components/run-trigger.md) | `src/uaw/run/trigger.py` |

## 模块联系

| 方向 | 关系与载荷 | 对应设计 |
| --- | --- | --- |
| 上游 → 本节点 | 调用：创建与控制执行 | [产品入口](../components/ingress.md) |
| 本节点 → 下游 | 调用：发起理解或修订 | [任务理解 · Intent](intent.md) |
| 上游 → 本节点 | 状态/事件：预算/检查点/完成申请 | [决策执行 · Agent](agent.md) |
| 上游 → 本节点 | 状态/事件：审批请求与用量 | [工具执行 · Tool](tool.md) |
| 上游 → 本节点 | 状态/事件：模型预算预留与结算 | [模型调用 · Model](model.md) |
| 本节点 → 下游 | 状态/事件：Items、进度、审批、成果 | [交互页面](../components/ui.md) |
| 本节点 → 下游 | 数据/引用：关联诊断与评测输入 | [共享支撑与控制层](support.md) |

## 参考与需要验证的选择

- [Runtime · 预算/deadline/checkpoint](https://app.notion.com/p/3f06ccd32c878070921ce42ff22e6257)：参考问题与原则，具体协议为 UAW 自己的设计。
- [Guardrails · durable审批](https://app.notion.com/p/3f06ccd32c878056b729e7a41fd4232b)：参考问题与原则，具体协议为 UAW 自己的设计。

题集是检查遗漏的来源，未逐题验证第三方技术结论。实施阶段涉及具体供应商协议时再核对其官方资料；本文的字段、算法顺序与权限边界不是从题集自动取得的事实。

