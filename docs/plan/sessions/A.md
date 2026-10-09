# Session A：集成与任务理解

[并行开发总入口](../PARALLEL.md)

状态：MS-I2i安排已发布：当前模型评估、文本成果与完成提交、逐包集成；运行来源ms-i2h-a3，原13实连/31聚焦回执保留，本包实现尚未验收。以DISPATCH的固定版本与派发为准。

## 工作位置和顺序

- 实际分支：`integration`。
- 实际worktree：`E:/UAW`。
- 首包：MS-00；后续：MS-I1、MS-I2a、MS-I2b、MS-I2c、MS-I2d、MS-I2e、MS-I2f1、MS-I2f2、MS-I2g、MS-I2h、MS-I2i、MS-I2f、MS-I2、MS-I3。
- 交接记录：[docs/coordination/handoffs/A.md](../../coordination/handoffs/A.md)。
- 公共变更提案目录：`docs/coordination/requests/A/`。

## 可修改路径

- `src/uaw/composition.py`
- `src/uaw/application.py`
- `src/uaw/shared/`
- `src/uaw/api/`
- `src/uaw/infrastructure/`
- `src/uaw/run/`
- `src/uaw/model/`
- `src/uaw/intent/`
- `src/uaw/agent/`
- `tests/unit/agent/`
- `tests/integration/agent/`
- `src/uaw/context/seed.py`
- `src/uaw/context/intent.py`
- `src/uaw/workspace/artifacts.py`
- `src/uaw/workspace/artifact_repository.py`
- `tests/unit/artifacts/`
- `tests/integration/artifacts/`
- `src/uaw/resources/`
- `contracts/`
- `planning/`
- `design/`
- `architecture/`
- `technology/`
- `ops/`
- `pyproject.toml`
- `uv.lock`
- `.python-version`
- `tests/conftest.py`
- `tests/integration/test_control_plane.py`
- `tests/integration/test_bootstrap.py`
- `tests/integration/model/`
- `tests/integration/intent/`
- `README.md`
- `DEVELOPMENT_PLAN.md`
- `.gitignore`
- `.gitattributes`
- `tests/integration/test_runner_control.py`
- `tests/integration/test_runner_receipt_wiring.py`
- `tests/integration/test_context_wiring.py`
- `tests/unit/model/`
- `tests/integration/test_runtime_sources.py`
- `tests/integration/test_stage_wiring.py`
- `tests/integration/test_approvals.py`
- `tests/unit/test_runner_signatures.py`
- `tests/integration/test_execution_permissions.py`
- `tests/integration/test_execution_leases.py`
- `tests/integration/test_model_input_routing.py`
- `tests/unit/shared/`
- `docs/plan/`
- `docs/api/`
- `docs/design/`
- `docs/technology/`
- `docs/implementation/`
- `docs/DOCUMENT_MAP.md`
- `docs/PROJECT_STRUCTURE.md`
- `docs/coordination/DISPATCH.md`
- `docs/coordination/HANDOFF_TEMPLATE.md`
- `docs/coordination/REQUEST_TEMPLATE.md`
- `docs/coordination/NEXT_WAVE.md`
- `docs/coordination/handoffs/A.md`
- `docs/coordination/requests/A/`

忽略的本session缓存、临时目录和测试回执可写；可修改路径以本session工作区为根。工作目录之外的其他worktree仍不可修改。

## 具体边界

- 负责现有P1-01收尾、公共契约、组装根、迁移、依赖锁和合并。
- 独立组件的业务错误交回对应负责人修复，A负责跨模块接线与冲突裁决。
- 逐包审阅、合并、回归；保持集成分支可启动，不同时接收多份公共改动。
- MS-C6/MS-T2e/MS-R2e组件已接受，当前MS-I2i负责模型评估/成果完成控制和公共适配；B/C/D以ms-i2i-start独立开发，阶段接口到即接线。

公共schema/port/依赖有缺口时，提交有字段、示例、错误语义和受影响调用方的提案，A合入并发布新基线后再使用；不在私有DTO中偷偷加不兼容字段。

## 对应工作包

### MS-00：收尾并建立共同基线

对应原轮：[P0-05](../rounds/P0-05.md)、[P1-01](../rounds/P1-01.md)。
开发前置：本session收尾与初始化工作。

任务：

1. 检查并结束遗留运行；完成当前P1-01的静态/真实PG边界检查，修复实际失败。
2. 同步契约源与生成物、已挂载入口与实现范围，记录真实模型仍待D06。
3. 检查忽略规则，初始化Git并创建本地基线提交；不提交.data、凭据、构建缓存或worktree。
4. 冻结schema/公开port/事件/失败/版本语义，记录真实提交SHA、依赖锁摘要和模块修改边界。
5. 分别配置B/C/D的worktree与环境，填写交接记录，变更dispatch_ready后才开工。

交付检查：

- 当前源码全量检查有新回执；历史60项不是当前P1-01的通过证明。
- Git实际可用，所有session基于相同真实提交SHA；当前工作已保留。
- 提供方未配置仍保留门槛，不把开发边界通过写成真实LLM验收。

### MS-I1：合入Context并接Intent/Model

对应原轮：[P1-01](../rounds/P1-01.md)、[P1-02](../rounds/P1-02.md)。
开发前置：MS-00、MS-C1。

任务：

1. 审阅B的目录/接口/证据，集中处理公共契约提案后合入。
2. 完成composition和Model输入port接线，处理现有context/intent.py与通用装配器的职责。
3. 验证输入修订、摘要权限、窗口/结构协议以及来源删除与撤销；保留实际P0/P1门槛。

交付检查：

- 组合回归通过，A/B对接线前后公开port样例达成一致。
- Context绑定、规则和引用实际一致；无真实LLM门槛时只验收开发范围。

### MS-I2a：持久人工审批和签名公共基础

对应原轮：[P1-03](../rounds/P1-03.md)、[P1-04](../rounds/P1-04.md)。
开发前置：MS-I1、MS-T1、MS-R1。

任务：

1. 实现真实SQL单次人工审批、认证查询/决定及执行前复核。
2. 发布ApprovalAuthorityPort/ApprovalPort/BudgetPort、Ed25519字节规则和互斥Runner回执，更新锁与真实测试。
3. 默认无Tool权限adapter则拒绝；拆出C/D可独立开发的子包，不声称完整MS-I2完成。

交付检查：

- 真实SQL和真实签名验证通过，公共服务实际满足port；无假批准/假执行。
- MS-T2a/MS-R2a有固定版本、明确范围及依赖缺失分支，原P1门槛继续保留。

### MS-I2b：实时父子权限链公共接线

对应原轮：[P1-02](../rounds/P1-02.md)、[P1-03](../rounds/P1-03.md)、[P1-04](../rounds/P1-04.md)。
开发前置：MS-I2a。

任务：

1. 提供ExecutionPolicyPort及严格ExecutionPolicySnapshot，读取当前主体真实持久父子政策，不注册或推断新权限。
2. 统一Context/Model/Approval的scope、当前revision/hash、八级父链、deny并集和能力/网络/资源收窄；非空未解析flag引用拒绝。
3. Model调用中父政策撤销停止本地工作，保留未知用量；修复公共gate提前检测时Intent的生命周期错误兼容。
4. 发布新集成版本和SQL组合验证，C/D继续ms-i2a，不要求开发中途切换。

交付检查：

- 真实SQL覆盖父deny/扩大/循环/深度/撤销/并发变化/快照转用；既有Context/Model/审批回归通过。
- snapshot不是可重放授权或dispatch租约；角色/flags/模型/预算/资源/Runner还需各所有者实际校验，不提前解锁完整MS-I2。

### MS-I2c：接受基础组件并发布恢复/异步消费接口

对应原轮：[P1-02](../rounds/P1-02.md)、[P1-03](../rounds/P1-03.md)、[P1-04](../rounds/P1-04.md)。
开发前置：MS-I2b、MS-T2a、MS-R2a。

任务：

1. 审阅合入C/D，修复Provider状态枚举和未知用量共享schema兼容。
2. 实现BudgetStatePort，发布ToolReconciliationReceipt/Reader和AsyncRunnerAuthorityPort/DTO；明确ModelPrompt公开消费边界。
3. 执行真实PG/密码学/静态全量回归；发布固定ms-i2c，三份下一包不互相消费未合入源码。

交付检查：

- C的17项真实SQL与D真实签名/跨进程一次消费通过，原回执保持。
- 读port有实际实现；生产receipt/authority缺失明确，无安装/写入/exec或假配对。

### MS-I2d：B/D组件接受、根执行租约与输入路由

对应原轮：[P1-02](../rounds/P1-02.md)、[P1-04](../rounds/P1-04.md)、[P1-09](../rounds/P1-09.md)。
开发前置：MS-I2c、MS-C3、MS-R2b。

任务：

1. 合入B/D，真实SQL复验通用模型输入并修测试Reader pin及Windows子进程兼容。
2. 实现根ExecutionLeasePort及真实PostgreSQL服务，当前holder/session、scope、CAS、单调fence、持久终态、取消清理与响应丢失重试。
3. 按真实存储命名空间路由Model输入，冲突拒绝；通用authority缺失不退回理解模板。
4. 验证调用期限与根租约隔离，发布固定ms-i2d；C当前包仍固定ms-i2c，B/D不强派依赖未满足的新包。

交付检查：

- 真实SQL并发/恢复/过期/取消/锁等待/旧holder验证通过，输入路由与原理解回归通过。
- lease不授权执行；真实设备/命令/IPC/authority仍待接线，无新能力flags或真实执行声明。

### MS-I2e：接受Tool核对组件并发布下一轮范围

对应原轮：[P1-03](../rounds/P1-03.md)、[P1-09](../rounds/P1-09.md)。
开发前置：MS-I2d、MS-T2b。

任务：

1. 合入C的MS-T2b，复跑97项单元与43项实际SQL，修复跨测试目录的模块名冲突。
2. 验证预算/政策port消费、实际回执与效果/费用分离、并发及新进程恢复；全量回归并核对源码摘要。
3. 发布ms-i2e和三个互不依赖开发分支的组件包，保留真实Reader/executor与原阶段门槛。

交付检查：

- 真实SQL/静态/全量回归通过，无隐藏失败/跳过；C原缺连接回执保留。
- C只接受组件范围；实际dispatch/配对/LLM不因此开放，A不改写worker分支。

### MS-I2f1：设备/命令登记及当前权威组件

对应原轮：[P1-03](../rounds/P1-03.md)、[P1-04](../rounds/P1-04.md)、[P1-09](../rounds/P1-09.md)。
开发前置：MS-I2e。

任务：

1. 实现平台拥有的设备/通道归属与CAS撤销、不可变原请求/签字命令和原attempt唯一登记。
2. 增加实际预算dispatch状态port；以原存储ctx组合当前政策/固定模型绑定/配置/预算/lease、独立根/动作gate/签名。
3. 组装Container内部服务，缺真实通道/根/审批/密钥后端不准入，不挂载HTTP/工具/执行。
4. 真实SQL与Ed25519验证响应丢失、并发、撤销/期限/伪造、取消后恢复和缺来源；详细范围见MS-I2f1-scope。

交付检查：

- 命令声明只作比对；通道/根/gate为明确受控组件测试源，不冒充真实配对/IPC/OS后端。
- 本子包接受与完整MS-I2f/阶段验收分开；worker开发中的基线继续ms-i2e。

### MS-I2f2：缓存/工具恢复/journal接受与登记Reader接线

对应原轮：[P1-02](../rounds/P1-02.md)、[P1-03](../rounds/P1-03.md)、[P1-04](../rounds/P1-04.md)、[P1-09](../rounds/P1-09.md)、[P4-04](../rounds/P4-04.md)。
开发前置：MS-I2f1、MS-C4、MS-T2c、MS-R2c。

任务：

1. 逐包合入B/C/D，实跑Context35和Tool70个真实SQL以及原签名/持久回归。
2. 组装可选纯计算缓存，默认关闭且当前权限/来源检查保留；统一journal固定Ref为content。
3. 从实际PostgreSQL命令和独立设备owner实现ReceiptCommandReader，恢复不重新准入或reserve/dispatch。
4. 验证跨模块签名journal恢复、撤销/取消/重启，发布固定基线；详细接口与目录见MS-I2f2-integration。

交付检查：

- SQL/静态/全量841项通过，无隐藏错误/跳过；原worker回执和提交保持。
- 仅组件接受；生产Lookup/Reader/executor和IPC/配对仍待依赖，不改变完整阶段状态。

### MS-I2g：独立验证环境/阶段接口接线/并行集成

对应原轮：[P0-02](../rounds/P0-02.md)、[P1-02](../rounds/P1-02.md)、[P1-03](../rounds/P1-03.md)、[P1-04](../rounds/P1-04.md)、[P1-07](../rounds/P1-07.md)。
开发前置：MS-I2f2。

任务：

1. 发布ms-i2g-start、完整功能包和A/B/C/D独立Docker project/端口/volume，验证A旧入口兼容。
2. 并行处理阶段版签名、公共提案与既有Run/政策/模型来源装配；领域实现归各worker，最终逐包合入。
3. 受影响模块和跨模块验证优先，worker实跑自己的模块SQL；全量只在集成里程碑或具体风险要求时扩跑。
4. 接通通用上下文/只读工具/签名根来源，列明channel/IPC/真实LLM及Agent循环剩余关键路径。

交付检查：

- 准备发布不代表三个包已开工/接受；记录阶段版和最终真实回执与SHA，原阶段门槛保留。
- 不存在worker互相依赖开发分支；生产来源和flags只在实际集成验收后开放。

### MS-I2h：根实例/有限步单Agent/阶段版集成

对应原轮：[P1-07](../rounds/P1-07.md)、[P1-08](../rounds/P1-08.md)、[P1-09](../rounds/P1-09.md)。
开发前置：MS-C5、MS-T2d、MS-R2d。

任务：

1. 当前Run/TaskFrame/固定用户模型/角色/预算/权限根Factory。
2. 内部AgentEnginePort与LangGraph封装，动态Context/Model/Tool/观察有限步循环。
3. waiting/审批/取消/期限/恢复和完成提案的实际证据核验；模型不得直接写completed。
4. 阶段版接口和公共提案即时处理，受影响跨模块验证，真实LLM和产品任务另验收。

交付检查：

- 先纯文本组件链，不强制依赖所有本机执行能力；公开入口按实际门槛开放。
- 所有子模型默认继承用户固定模型；本轮不默认子树/DAG。

### MS-I2i：固定模型评估/成果核验/完成提交与逐包集成

对应原轮：[P1-02](../rounds/P1-02.md)、[P1-07](../rounds/P1-07.md)、[P1-08](../rounds/P1-08.md)、[P1-09](../rounds/P1-09.md)。
开发前置：MS-C6、MS-T2e、MS-R2e。

任务：

1. M1实际TaskFrame/固定Model/规则成果Ref到有界评估输入，规则评估与语义校验共用来源边界；B接口到达优先做SQL适配。
2. M2真实文本MarkdownArtifact、逐项VerificationReport、DeliveryProposal和独立Run终态CAS，缺证据/测试不passed。
3. M3阶段SHA到即审阅/接线，合法本地工具provider/角色/executor/verifier，D独立通道/映射；不等三包齐才处理。
4. M4真实DeepSeek办公/数据/学术/多规则/修订取消/错误引用样例，保存全尝试费用；汇合后一次全量，完整P1门槛保留。

交付检查：

- 运行输入为ms-i2h-a3，四包固定ms-i2i-start；纯数据成果链不等待D，worker自己实跑模块SQL。
- 普通worker不能直接completed；公开API/flags依真实门槛，未完成来源明确不可用，不默认子Agent/DAG。

### MS-I2f：实际设备归属、登记命令与当前权威

对应原轮：[P1-03](../rounds/P1-03.md)、[P1-04](../rounds/P1-04.md)、[P1-09](../rounds/P1-09.md)。
开发前置：MS-I2f2。

任务：

1. 实现有来源的设备/通道归属和不可变请求/命令登记；认证服务入口不消费模型自报owner或授权。
2. 先发布对象/port/错误/撤销与恢复读取语义，再从实际记录组装当前权限/配置/预算审批/根/lease/fence的AsyncRunnerAuthority。
3. 给通用Context与Tool/Runner实际Reader补明确接线；按包边界接受B/C/D，不在worker开发中途强迫同步。
4. 真实SQL验证拥有者/版本/参数/lease/撤销，缺配对/可信通道/资源来源拒绝；IPC/OS凭据和D03另过门槛。

交付检查：

- authority来自实际独立拥有者数据，不回显command自报ctx；签名密钥不进普通记录。
- lease与权限/准入不同，恢复不新建动作；实际IPC/exec未通过时继续关闭。

### MS-I2：合入Tool与Runner并完成真实权威接线

对应原轮：[P1-03](../rounds/P1-03.md)、[P1-04](../rounds/P1-04.md)。
开发前置：MS-I2f、MS-T2c、MS-R2c。

任务：

1. 分别审阅合入C/D基础包，统一批准契约/依赖/数据库变更。
2. 确认审批、预算、配置、Runner调用port及调用顺序；修跨边界失败返回。
3. 发布第二个集成SHA供C/D同步；真实执行仍等待后续接线和授权。

交付检查：

- 三模块接口消费方检查通过；不是把签名/执行替身当真实Runner。
- D03选择及提供方配置的未满足项仍可见。

### MS-I3：汇合后进入Agent闭环

对应原轮：[P1-07](../rounds/P1-07.md)、[P1-08](../rounds/P1-08.md)、[P1-09](../rounds/P1-09.md)、[P1-11](../rounds/P1-11.md)。
开发前置：MS-C2、MS-T2、MS-R2。

任务：

1. 统一跨模块回归，检查原始完整轮的依赖与真实模型/环境门槛。
2. 按P1-06/07/08/09/10/11原计划接变更、Agent、完成核验、用户控制和页面。
3. 此包是后续汇合入口；不能代替尚未展开的页面与闭环轮。

交付检查：

- 50轮主计划的退出标准保持有效。
- 真正的P1阶段验收需真实用户授权、测试、成果和审阅证据。

## 当前session开工说明

沿用已有聊天与独立worktree，粘贴本session说明。A先在DISPATCH公布真实基线SHA和派发包。

```text
你负责UAW并行开发中的Session A：集成与任务理解。
当前工作目录必须是E:/UAW，分支必须是integration。
先阅读README.md、docs/plan/PARALLEL.md、docs/plan/PARALLEL_WORKFLOW.md和docs/plan/sessions/A.md。
读取docs/coordination/DISPATCH.md。本轮核对HEAD与ms-i2i-start解析出的commit相同；后续在包边界按A发布的新基线同步。
当前在integration执行集成任务，不替worker同步或重写分支。
只修改session页的允许目录。涉及公共文件，写入本session requests目录，说明最小变更与消费方影响。
按照工作包完成代码和必要验证，未实现依赖明确返回不可用；测试替身不冒充真实LLM/Runner。
保持原文、固定用户模型、权限/flag、取消、幂等及版本边界。未经确认的D01/D03/D06不自行设定。
在handoff记录写实际分支与提交SHA、改动文件、公开接口、验证命令/回执、未通过项和接线要求。
开发session只提交自己的改动。A审阅、合入、处理公共冲突并执行整条链路回归。不要自行创建其他session。
```
