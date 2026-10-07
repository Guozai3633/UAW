# 工作区 · Workspace：模块开发设计

节点 `workspace` · UAW v0.10 · 2026-10-07 · 状态：目标设计，Runtime 未实现。

[开发设计索引](../README.md) · [目录设计](../../PROJECT_STRUCTURE.md) · [公共契约](../COMMON_CONTRACTS.md)

## 统一入口与状态所有权

计划包：`src/uaw/workspace/`，入口：`src/uaw/workspace/facade.py`。

入口契约：`WorkspaceRuntime.allocate(WorkspaceSpec)、prepare(EnvironmentRequest)、merge(MergeRequest)、review/revert(ChangeRequest)`。

所有权：项目绑定、基础快照、隔离分支、环境/进程、ChangeSet、Artifact/ReviewSet。

## 内部组织策略

本地绑定明确设备/根与能力；基础状态包括获准未提交修改；并行写隔离，原生模式明确权限；真实环境ready后执行并采集改动；合并/局部接受/撤销核对用户当前版本，再形成受控成果和重验。

facade接收可信请求并协调子组件；子组件不直接调用其他Runtime的私有实现。只通过注入的port调用邻域公开入口。Python首阶段组合在同一进程内，持久化和本地Runner执行仍通过边界接口。

## 数据与依赖接口

输入：项目授权、BaseState、操作与预期版本。输出：Environment、ChangeSet、Artifact、ReviewSet。

注入ports：`LocalRunnerClient、CloudSandboxAdapter、Policy/BudgetPort、ProcessExecutor、Snapshot/Change/Artifact/ReviewRepository、FormatAdapters`。

领域类型放本包 contracts.py；模型可见工具schema由Tool消费。Repository不暴露其他模块可任意写本模块对象的方法，修改必须走本模块业务入口。

## 决策、权限与资源策略

代码写作与冲突修复方案由Agent提出；实际文件/进程、三方合并、范围与版本检查由代码，语义冲突无法确认交用户。

本地 Runner 再检查；cwd/venv 不等于安全隔离。

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

Runner越界、未提交内容快照、shell改动采集、真实test退出码、用户改动保留与撤销。

首条真实任务贯通入口/核心子组件；其他节点先保留port，未实现能力不暴露为可调用工具。细分模块策略与验收案例见下面各文档。

## 逐字段接口与对象定义

[本节点全部接口](../../api/nodes/workspace.md) · [统一对象字典](../../api/OBJECTS.md) · [接口共同规则](../../api/CONVENTIONS.md)

上面的领域字段用于说明策略。准确请求DTO、动作分支、必填性、返回对象和结构规则以接口契约源contracts/interface_catalog.py及其生成schema为准；语义/权限/版本/执行策略仍按本设计落实。出现差异需同时修维护源，不能拿摘要字段替代当前接口校验。

## 内部模块与目录

| 子模块 | 详细开发策略 | 计划代码文件 |
| --- | --- | --- |
| 项目绑定与本地授权 | [workspace.binding](../components/workspace-binding.md) | `src/uaw/workspace/binding.py` |
| 输入基础状态 | [workspace.base](../components/workspace-base.md) | `src/uaw/workspace/base.py` |
| 隔离与分支 | [workspace.isolation](../components/workspace-isolation.md) | `src/uaw/workspace/isolation.py` |
| 环境准备与回收 | [workspace.environment](../components/workspace-environment.md) | `src/uaw/workspace/environment.py` |
| 文件与进程执行 | [workspace.process](../components/workspace-process.md) | `src/uaw/workspace/process.py` |
| 变更与冲突合并 | [workspace.changes](../components/workspace-changes.md) | `src/uaw/workspace/changes.py` |
| 产物与格式适配 | [workspace.artifacts](../components/workspace-artifacts.md) | `src/uaw/workspace/artifacts.py` |
| 审阅与局部接受 | [workspace.review](../components/workspace-review.md) | `src/uaw/workspace/review.py` |

## 模块联系

| 方向 | 关系与载荷 | 对应设计 |
| --- | --- | --- |
| 上游 → 本节点 | 调用：受控文件/环境/进程 | [工具执行 · Tool](tool.md) |
| 上游 → 本节点 | 调用：隔离分配与交付协调 | [决策执行 · Agent](agent.md) |
| 本节点 → 下游 | 数据/引用：授权文件与产物版本 | [上下文 · Context](context.md) |

## 参考与需要验证的选择

- [Runtime · 执行环境/恢复](https://app.notion.com/p/3f06ccd32c878070921ce42ff22e6257)：参考问题与原则，具体协议为 UAW 自己的设计。
- [Guardrails · 沙箱/本地边界](https://app.notion.com/p/3f06ccd32c878056b729e7a41fd4232b)：参考问题与原则，具体协议为 UAW 自己的设计。

题集是检查遗漏的来源，未逐题验证第三方技术结论。实施阶段涉及具体供应商协议时再核对其官方资料；本文的字段、算法顺序与权限边界不是从题集自动取得的事实。

