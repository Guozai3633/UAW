# Session C：工具组件

[并行开发总入口](../PARALLEL.md)

状态：MS-T2g已发布待开工：file.read工具与真实结果恢复；MS-T2f组件接受，不重做原包。以DISPATCH的固定版本与派发为准。

## 工作位置和顺序

- 实际分支：`dev/tool`。
- 实际worktree：`E:/UAW/.worktrees/tool`。
- 首包：MS-T1；后续：MS-T2a、MS-T2b、MS-T2c、MS-T2d、MS-T2e、MS-T2f、MS-T2g、MS-T2。
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
- 本轮MS-T2g实现已有file.read的工具执行/核验/恢复；A注入控制端，缺真实来源不可用，不自行开启flags或写入安装exec。

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

### MS-T2d：只读工具调用编排/实际adapter/持久结果源

对应原轮：[P1-03](../rounds/P1-03.md)、[P1-09](../rounds/P1-09.md)。
开发前置：MS-I2f2。

任务：

1. 以现有审批/预算/账本串联invoke闸门和持久发送所有权，内部可选executor消费固定call/spec/ctx。
2. 实现有界实际text.inspect只读adapter及输出schema/真实响应保存，不依赖D新IPC或注册为产品目录。
3. 实现固定结果source的publish/Lookup/Reader，规范ToolResult并接已有reconcile/read_outcome，效果与费用独立恢复。
4. 独立SQL覆盖waiting/拒绝/批准、一次发送、并发/重启、超时取消/响应丢失、输出错误和费用中断，原70项SQL回归。

交付检查：

- 阶段版后继续同包恢复与验证；无executor先拒绝，未知发送不重新attempt，缺生产权限仍不可用。
- 真实本地只读结果有证据，不从Runner回执或传输200推断成功；完整MS-T2/P1仍待集成。

### MS-T2e：权限先行混合检索/向量索引缓存

对应原轮：[P1-03](../rounds/P1-03.md)。
开发前置：MS-T2d、MS-I2f2。

任务：

1. 当前role/权限/flag/环境/provider先过滤ToolRegistry固定快照。
2. 显式embedding port、词法/向量召回与有界融合；返回既有DiscoveryResult，LLM选择工具。
3. 结构化SQLite向量索引缓存原子更新/失效/重启；索引不是目录或权限权威。
4. 自身SQL及索引测试覆盖等待期间权限变化、损坏/并发/泄漏和原工具结果回归。

交付检查：

- 无embedding不冒充语义向量；lexical-only或降级由构造显式配置。
- 不执行工具或修改固定模型，阶段版后继续完整包。

### MS-T2f：办公计算/JSON检查/多适配器持久恢复

对应原轮：[P1-03](../rounds/P1-03.md)。
开发前置：MS-T2e。

任务：

1. M1实现有界Decimal arithmetic.calculate与data.inspect_json，完整Spec、实际executor/verifier与阶段签名。
2. M2按精确ToolRef构造有限executor/verifier路由，拒绝未知/改版/重复绑定，text.inspect默认兼容。
3. M3消费原审批/预算/账本/实际receipt与恢复来源，支持纯参数resource adapter，unknown不换attempt重发。
4. M4自身55434实跑新工具+原text/检索/索引，参数变化/篡改/并发/撤销取消/重启与费用恢复。

交付检查：

- 不eval、脚本、网络、本机文件或exec；A配置合法本地provider/角色/目录并跑真实模型选择。
- M1/M2阶段交付后继续完整包；不依赖D开发分支，不把工具成功当任务完成。

### MS-T2g：真实file.read工具/签名语义核验/原结果恢复

对应原轮：[P1-03](../rounds/P1-03.md)、[P1-04](../rounds/P1-04.md)、[P1-08](../rounds/P1-08.md)。
开发前置：MS-T2f、MS-R2f。

任务：

1. M1消费既有file.read/FileContent，固定完整Spec与C到A桥接/恢复签名。
2. M2沿审批预算一次发送精确路由，核对原command/attempt/签名/路径/范围/UTF8/hash/游标。
3. M3持久实际文件观察与费用，原journal恢复，unknown不重发，数据权限与新准入分开。
4. M4自身真实SQL和临时测试根覆盖分页/变化/篡改/跨项目主体/撤销取消/并发重启。

交付检查：

- 仅C Tool与自身测试；A注入实际控制端，不依赖D开发分支或伪造用户根授权。
- 签名或Runner ok不能替代数据核验，片段hash不冒称完整hash，不开写入安装exec。

### MS-T2：工具真实dispatch及结算接线

对应原轮：[P1-03](../rounds/P1-03.md)、[P1-09](../rounds/P1-09.md)。
开发前置：MS-I2、MS-T2a。

任务：

1. 在A提供真实预算/审批/Runner port后实现dispatch意图、结果规范和结算。
2. 验证审批后参数/资源变化、重复调用、取消、unknown写效果与有限安全恢复。

交付检查：

- 缺少真实依赖时返回等待/不可用，不扩权限绕过。
- 完整P1-03验收按原轮依赖与门槛，不能只凭组件用例通过。

## 当前session开工说明

沿用已有聊天与独立worktree，粘贴本session说明。A先在DISPATCH公布真实基线SHA和派发包。

```text
你负责UAW并行开发中的Session C：工具组件。
当前工作目录必须是E:/UAW/.worktrees/tool，分支必须是dev/tool。
先阅读README.md、docs/plan/PARALLEL.md、docs/plan/PARALLEL_WORKFLOW.md和docs/plan/sessions/C.md。
读取docs/coordination/DISPATCH.md。本轮核对HEAD与ms-i2j-start解析出的commit相同；后续在包边界按A发布的新基线同步。
当前执行MS-T2g。工作区干净后fetch origin --tags，使用git merge --ff-only ms-i2j-start同步本工作分支；失败先报告，不reset，保留已有历史。
只修改session页的允许目录。涉及公共文件，写入本session requests目录，说明最小变更与消费方影响。
按照工作包完成代码和必要验证，未实现依赖明确返回不可用；测试替身不冒充真实LLM/Runner。
保持原文、固定用户模型、权限/flag、取消、幂等及版本边界。未经确认的D01/D03/D06不自行设定。
在handoff记录写实际分支与提交SHA、改动文件、公开接口、验证命令/回执、未通过项和接线要求。
开发session只提交自己的改动。A审阅、合入、处理公共冲突并执行整条链路回归。不要自行创建其他session。
```
