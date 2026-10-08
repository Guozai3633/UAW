# Session C：工具组件

[并行开发总入口](../PARALLEL.md)

状态：MS-T2b已接受且43项SQL复验通过；MS-T2c补统一核对入口与明确outcome读取。以DISPATCH的固定版本与派发为准。

## 工作位置和顺序

- 实际分支：`dev/tool`。
- 实际worktree：`E:/UAW/.worktrees/tool`。
- 首包：MS-T1；后续：MS-T2a、MS-T2b、MS-T2c、MS-T2。
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

### MS-T2a：持久调用账本和审批适配

对应原轮：[P1-03](../rounds/P1-03.md)、[P1-09](../rounds/P1-09.md)。
开发前置：MS-I2a。

任务：

1. 消费A的ApprovalPort/BudgetPort，实现可信固定动作/资源的ApprovalAuthorityPort；未授权Reader明确不可用。
2. 实现持久action/attempt/dispatch意图/effect账本和预算阶段恢复，不在同一会话锁内嵌套调用预算服务。
3. 补真实SQL重启/并发/审批参数变化/取消/unknown测试；公共DTO变更在C提案目录交A。

交付检查：

- 真实审批与预算可消费；等待引用真实，未知写效果不重发，测试adapter不注册产品。
- 无Runner/executor保持不可用，不自动进入完整MS-T2或宣布P1-03接受。

### MS-T2b：预算接口收敛和可信结果核对

对应原轮：[P1-03](../rounds/P1-03.md)、[P1-09](../rounds/P1-09.md)。
开发前置：MS-I2c。

任务：

1. 注入BudgetStatePort替换跨所有者budget.*读取；消费ExecutionPolicyPort替换重复父链决策并保留角色/资源/配置检查。
2. 实现ToolReceiptReaderPort驱动的核对入口，验证固定action/attempt/provider/receipt、usage和实际证据；持久核对计划与CAS去重。
3. 独立处理效果与费用，unknown不重发，not_applied不推定零用量；允许原attempt账务恢复但不新准入。
4. 真实SQL验证重启、响应丢失、重复/冲突回执、并发核对、撤销/取消、Reader缺失与unknown保留；不接真实dispatch。

交付检查：

- 不直接读取A预算私有表，不用超时/预算状态推断副作用。
- 受控Reader明示组件范围；没有生产Reader/executor返回不可用，完整MS-T2继续等待。

### MS-T2c：统一核对入口与效果结论读取

对应原轮：[P1-03](../rounds/P1-03.md)、[P1-09](../rounds/P1-09.md)。
开发前置：MS-I2e。

任务：

1. ToolFacade.reconcile消费现有ReconcileRequest和RuntimeToolruntimeReconcileResult；通过可选ActionReceiptLookupPort找到原attempt实际固定回执。
2. 继续交ToolReconciler严校验Reader/证据/绑定/CAS/费用，缺port/无来源不推断未应用，不新建attempt或reserve/dispatch。
3. 提供read_outcome返回实际已接受且当前可读的ToolReconciliationReceipt；confirmed/核对ok不等于applied或Task成功。
4. 真实SQL覆盖查找/越权/重启/重复/撤销/取消恢复和效果费用独立；不改schema/HTTP/flags。

交付检查：

- 内部Lookup只返回已登记原尝试来源，不接受模型额外receipt_ref；生产Lookup由A接线。
- 保留43项SQL和unknown语义，无新增执行/重试授权；精确接口见MS-I2e-next-packages。

### MS-T2：工具真实dispatch及结算接线

对应原轮：[P1-03](../rounds/P1-03.md)、[P1-09](../rounds/P1-09.md)。
开发前置：MS-I2、MS-T2a。

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
当前执行MS-T2c。工作区干净后fetch origin --tags，使用git merge --ff-only ms-i2e同步本工作分支；失败先报告，不reset，保留已有历史。
只修改session页的允许目录。涉及公共文件，写入本session requests目录，说明最小变更与消费方影响。
按照工作包完成代码和必要验证，未实现依赖明确返回不可用；测试替身不冒充真实LLM/Runner。
保持原文、固定用户模型、权限/flag、取消、幂等及版本边界。未经确认的D01/D03/D06不自行设定。
在handoff记录写实际分支与提交SHA、改动文件、公开接口、验证命令/回执、未通过项和接线要求。
开发session只提交自己的改动。A审阅、合入、处理公共冲突并执行整条链路回归。不要自行创建其他session。
```
