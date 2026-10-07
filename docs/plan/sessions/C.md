# Session C：工具组件

[并行开发总入口](../PARALLEL.md)

状态：独立分支/worktree及依赖已准备。首包已分配，开发聊天尚未创建；开工先核对parallel-wave-1和DISPATCH。

## 工作位置和顺序

- 实际分支：`dev/tool`。
- 实际worktree：`E:/UAW/.worktrees/tool`。
- 首包：MS-T1；后续：MS-T2。
- 交接记录：[docs/coordination/handoffs/C.md](../../coordination/handoffs/C.md)。
- 公共变更提案目录：`docs/coordination/requests/C/`。

## 可修改路径

- `src/uaw/tool/`
- `tests/unit/tool/`
- `tests/integration/tool/`
- `docs/coordination/handoffs/C.md`
- `docs/coordination/requests/C/`

忽略的本session缓存、临时目录和测试回执可写；可修改路径以本session工作区为根。工作目录之外的其他worktree仍不可修改。

## 具体边界

- 先做小工具目录、schema规范化、角色/权限/flag过滤和动作身份。
- 审批、预算、配置、Runner通过公开port；未提供真实执行器时不得dispatch。
- 不放开禁用flag，不把测试适配器登记为产品工具；向量/MCP仍属后续轮。

公共schema/port/依赖有缺口时，提交有字段、示例、错误语义和受影响调用方的提案，A合入并发布新基线后再使用；不在私有DTO中偷偷加不兼容字段。

## 对应工作包

### MS-T1：工具注册、过滤与参数校验

对应原轮：[P1-03](../rounds/P1-03.md)。
开发前置：MS-00。

任务：

1. 实现ToolSpec固定版本登记/读取与已实现adapter绑定状态。
2. 先按角色/能力/feature flag/环境过滤候选，再按小目录搜索；模型保持最终选择权。
3. 实现严格参数schema、有界注册、动作参数摘要和action/attempt区分。
4. 定义precheck/recheck依赖port并返回可核验的拒绝/等待；没有批准与执行器不派发。

交付检查：

- 关闭工具直接伪造调用也不能执行；模型不能自报owner/approved。
- effect取自可信ToolSpec，同ID改参数冲突，未知写效果不盲重试。
- 测试adapter不作为产品能力发布；完整审批/dispatch验收留给接线包。

### MS-T2：意图/效果账本与审批接线

对应原轮：[P1-03](../rounds/P1-03.md)、[P1-09](../rounds/P1-09.md)。
开发前置：MS-I2。

任务：

1. 在A提供真实预算/审批/Runner port后实现dispatch意图、结果规范和结算。
2. 验证审批后参数/资源变化、重复调用、取消、unknown写效果与有限安全恢复。

交付检查：

- 缺少真实依赖时返回等待/不可用，不扩权限绕过。
- 完整P1-03验收按原轮依赖与门槛，不能只凭组件用例通过。

## 可复制到新session的开工说明

下面只启动本session任务；用户在独立工作区新建聊天后粘贴。A先在DISPATCH公布真实基线SHA和派发包。

```text
你负责UAW并行开发中的Session C：工具组件。
当前工作目录必须是E:/UAW/.worktrees/tool，分支必须是dev/tool。
先阅读README.md、docs/plan/PARALLEL.md、docs/plan/PARALLEL_WORKFLOW.md和docs/plan/sessions/C.md。
读取docs/coordination/DISPATCH.md。首次开工核对HEAD与parallel-wave-1解析出的commit相同；后续按A发布的新基线同步。
若基线未发布，先完成本包可做的设计/提案；不要修改或使用其他session未交接的源码。
只修改session页的允许目录。涉及公共文件，写入本session requests目录，说明最小变更与消费方影响。
按照工作包完成代码和必要验证，未实现依赖明确返回不可用；测试替身不冒充真实LLM/Runner。
保持原文、固定用户模型、权限/flag、取消、幂等及版本边界。未经确认的D01/D03/D06不自行设定。
在handoff记录写实际分支与提交SHA、改动文件、公开接口、验证命令/回执、未通过项和接线要求。
开发session只提交自己的改动。A审阅、合入、处理公共冲突并执行整条链路回归。不要自行创建其他session。
```
