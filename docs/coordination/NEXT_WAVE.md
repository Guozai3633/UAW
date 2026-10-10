# 当前可转发开工消息：MS-I2j（2026-10-10）

**只转发[MS-I2j四份提示词](MS-I2j-messages.md)。**统一固定ms-i2j-start；B本轮转apps/web前端，C做file.read工具，D做native目录授权，A做用户入口/API与集成。
[完整输入输出、目录与四个里程碑](requests/A/MS-I2j-parallel-packages.md)。开发基线不冒称MS-I2i完整回归已通过；旧回归由A先收尾。用户转发开工，A未替其他worker同步或发送聊天消息。

## 以下为历史派发原文，不作为本轮任务

# 下一轮可直接转发：MS-I2i（2026-10-09）

固定开工标签 **ms-i2i-start**；实际SHA与远程发布结果见[DISPATCH](DISPATCH.md)。来源为已验收的ms-i2h-a3；本次只准备安排，不把新包记成已开发或已接受。原B/C/D worktree已只读核对且干净，由各session自行在包边界同步，A没有替它们改分支或发消息。

[全部输入输出、策略、四个里程碑与目录](requests/A/MS-I2i-parallel-packages.md)。本轮四个包都连续完成M1至M4；M1尽早交阶段接口，M2交源码/样例后继续本包，A同步接线并逐包接受。模块SQL由worker实跑，全量在最终集成里程碑执行。

## 发给A：MS-I2i

```text
开始UAW Session A本轮MS-I2i：当前固定模型评估、文本/Markdown成果登记、完成校验与逐包集成。
继续E:/UAW、integration，读取MS-I2i-parallel-packages.md第1/2/6/7节、DISPATCH及session/A。B/C/D用固定ms-i2i-start独立开发；不替它们切分支、同步或重写提交。
连续完成：1实际TaskFrame/固定Model/来源到有界评估输入，分别接规则评估和语义核验，避免多规则Context递归；B阶段批读接口到达即优先做A SQL适配。2实际文本/MarkdownArtifact、逐项VerificationReport、DeliveryProposal与独立Run完成控制器；缺证据/测试不能passed，取消/版本/unknown外部效果复核，用户接受按合同需要。3阶段SHA到即审阅/接线，合法本地工具provider/角色、实际executor/verifier及D独立通道映射；组件实现错误交原worker修。4真实DeepSeek办公/学术/多规则/修订取消样例，记录全部失败/成本，最终组件汇合后一次全量。
默认同用户模型，不开启子Agent/DAG/本机写入安装exec。公开接口/flags只有实际门槛通过再决定；未完成来源明确不可用。只改A保留路径及本轮新增artifacts文件，保留旧验收回执和标签。
```

## 发给B：MS-C7

```text
开始UAW Session B完整能力包MS-C7：Context读取提速与来源复查。
继续E:/UAW/.worktrees/context、dev/context。干净后git fetch origin --tags、git merge --ff-only ms-i2i-start，核对HEAD等于标签commit，uv sync --frozen；失败保留现场不reset/rebase。读MS-I2i-parallel-packages.md第1/2/3/7节、DISPATCH和session/B。
连续四项：1实际SQL测量单/多规则、有/无工具、冷暖缓存的get/SQL往返/Reader/assessor和build/ModelInput耗时，M1尽早固定ContextRecordBatchPort/RecordReadKey及阶段说明。2精简重复资料展开与纯计算，一次操作内有界批读，不缓存授权/取消/撤销，公开入口与模型/外部等待后及提交/派发前复查保留。3接可选批读port并证明消息/正文/引用/拒绝等价；A负责SQL适配，无适配用已声明的兼容策略，batch-required缺依赖明确不可用，不阻塞原路径开发。4自身55433真实SQL/新进程/并发/修订删除/撤销/跨主体/批缺失回归和测量报告。
M1发MS-C7-stage-interface.md，M2阶段源码与样例提交后继续M3/M4，A此时即可接线。只改B允许Context文件（seed.py/intent.py归A）、B测试/requests/handoff；不在Context写ORM、不改shared/Run/Model/composition/锁/flags。
在自己的PowerShell . ./ops/start-dev-db.ps1 -Session B，锁定环境迁移及--require-postgres实跑，回执写ignored tests/.artifacts/B/MS-C7；不复制A凭据或改别的库。保留失败，最终源码与handoff分开提交，干净交付；不自动下一包。
```

## 发给C：MS-T2f

```text
开始UAW Session C完整能力包MS-T2f：两个办公数据工具与多适配器执行/验证/恢复。
继续E:/UAW/.worktrees/tool、dev/tool。干净后fetch tags、merge --ff-only ms-i2i-start，核对HEAD/tag commit，uv sync --frozen；失败不reset/rebase。读MS-I2i-parallel-packages.md第1/2/4/7节、DISPATCH及session/C。
连续四项：1实际arithmetic.calculate@1（有界Decimal操作，禁止eval/脚本）和data.inspect_json@1（有界JSON、重复键/非有限数/深度检查），完整Spec/函数/executor/verifier，M1固定参数及构造。2按完整ToolRef由可信bindings有限路由executor/verifier，未知/改版/重复/提供方不符拒绝，保持text.inspect兼容。3消费原审批/预算/一次发送/真实receipt/结果发布与恢复；可增纯参数resource/recovery adapter，缺来源拒绝，unknown不换attempt重做。4自身55434真实SQL的两个工具+原text链、混合路由/篡改/撤销取消/并发/重启/费用中断回归，原检索/索引兼容。
M1交C-009-ms-t2f-stage-tools.md，M2源码及样例后继续M3/M4；A负责合法本地provider、角色、目录、组装及真实DeepSeek选择，不把聊天API当本地执行器。只改C允许Tool/测试/requests/handoff，不依赖D开发分支、不开flags或本机权限、不改用户模型/shared/锁。
本worktree . ./ops/start-dev-db.ps1 -Session C，迁移及--require-postgres实跑，ignored tests/.artifacts/C/MS-T2f保存所有回执。最终源码/handoff分开提交、干净交付；组件成功不等于任务完成，不自动扩包。
```

## 发给D：MS-R2f

```text
开始UAW Session D完整能力包MS-R2f：Windows同机可信IPC与只读Runner组件接入。
继续E:/UAW/.worktrees/runner、dev/runner。干净后fetch tags、merge --ff-only ms-i2i-start，核对HEAD/tag commit并uv sync --frozen；失败保留现场。读MS-I2i-parallel-packages.md第1/2/5/7节、DISPATCH及session/D。
连续四项：1真实Windows双进程命名管道、显式本机登录主体ACL/独立OS身份与对端生命周期、nonce/当前角色key签名及256KiB/10秒有界帧，M1先交构造和关闭/错误语义。2可信connection registry适配既有RunnerChannelSourcePort；owner/actor/device/key来自独立登记，不从body自证，断连/到期/进程退出/撤销失效，重连新Ref。3原已登记command到ReadOnlyRunner临时根，保留签名/authority/Root/lease/fence/一次使用和签名journal，IPC收取实际receipt。4真实双进程的冒名/坏签名/重放/断帧/超长/超时取消/退出重连/回复丢失后恢复与原D回归，清理随机OS凭据、管道和子进程。
M1交MS-R2f-stage-ipc.md，M2阶段源码后继续M3/M4。只改D允许workspace四文件/local_runner/测试/requests/handoff；A控制端和组装归A。标准库/ctypes优先，新依赖先提案；后台helper隐藏启动，不打印私钥。需要SQL才用本session55435，回执ignored tests/.artifacts/D/MS-R2f。
这是Windows开发通道，不替D03作正式部署决定；native用户确认仍独立，临时授权测试依赖明确标注，通信成功不冒充真实用户配对。不得访问用户项目、开启flags、写入安装exec；未知command不自动重发。最终源码/handoff分开提交、干净交付，不自动下一包。
```

## 历史状态（以下不作为新包派发）

# 当前交付状态：MS-I2h-A3（2026-10-09）

A已接入用户指定DeepSeek-V4.1-Flash，三个最终有界样例通过，13次调用含原失败，31不同聚焦检查通过。B/C/D原组件接受保持；新包未派发，完整MS-I2h/P1、成果完成校验和生产来源继续。A未改worker分支或发聊天消息；ms-i2h-start及旧标签不移动。

[实际记录](../implementation/MS-I2h-A3.md) · [证据索引](../implementation/evidence/ms-i2h-a3.json)。

## 历史状态（保留）

# 当前交付状态：MS-I2h-A2（2026-10-09）

B/MS-C6、C/MS-T2e、D/MS-R2e已按组件范围接受，A集成阶段421不同聚焦节点通过。代码/证据提交14f844253ab3ddc3b1366fa989e5c1cb7a3573ef，固定阶段标签ms-i2h-a2。新包未派发，不自动重做原包或接完整MS-T2/MS-R2。需要换基线时在包边界由worker自行fetch/快进同步；A不改worker分支。当前A准备真实DeepSeek凭据/模型和剩余实际来源，完整MS-I2h/P1仍待验收。

[最新接受记录](DISPATCH.md) · [阶段报告](../implementation/MS-I2h-A2.md) · [隐藏录入/真实验收](../implementation/DEEPSEEK_ACCEPTANCE.md)。

## 历史派发说明（保留）

# 下一轮可直接转发：MS-I2h

日期2026-10-08。B/MS-C5、C/MS-T2d、D/MS-R2d三个最终组件已接受；A在B最终合入后2条实际组装复验通过。新包共同固定开发基线 **ms-i2h-start**（实际SHA见[DISPATCH](DISPATCH.md)；git rev-parse标签核对）。完整MS-I2g/1077节点随后已由A通过；验收标签ms-i2g另发，worker仍用ms-i2h-start。旧任务下移为历史记录，不再重做。

[完整输入输出/策略/四里程碑/目录](requests/A/MS-I2h-parallel-packages.md)。以下分别转发给B、C、D；A没有发送其他聊天消息或替worker同步。

## 发给B：MS-C6

```text
开始UAW Session B完整能力包MS-C6：多规则语义评估接入、固定版本复查与真实读取成本测量。
继续E:/UAW/.worktrees/context、dev/context。工作区干净后fetch origin --tags、git merge --ff-only ms-i2h-start，核对HEAD等于标签commit；uv sync --frozen。失败报告，不reset/rebase。读MS-I2h-parallel-packages.md第1/2/6节、DISPATCH及session/B目录边界。
连续完成四项：1固定实际规则候选和可选assessor port；2多规则冲突/优先级/精确引用解析、模型等待前后来源复查；3登记→snapshot→ModelPrompt/引用整链与读取次数/耗时比较；4自身真实SQL的修订/撤销/并发/重启/缓存和原模块回归。前两项提交固定接口、示例和SHA，再继续同包，不等A最终合入。
RegisteredRuleProvider(inputs,*,assessor=None)保留旧构造；assessor只做语义建议，不改rule正文/level/scope/Ref，不授权。缺来源多规则不可用，不用词典冒充语义。A负责实际固定Model adapter，受控评估器不证明LLM质量。优化不能缓存权限或去掉取消/撤销/提交复查。
只改B允许路径。自己的PowerShell dot-source ops/start-dev-db.ps1 -Session B，再锁定环境alembic upgrade head，独立55433实跑模块SQL，ignored回执保留失败及修复。公共缺口提案交A，继续独立部分。阶段和最终源码/handoff分开提交，干净后交付；不改flags/Model/shared/锁/组装根，不自动扩包。
```

## 发给C：MS-T2e

```text
开始UAW Session C完整能力包MS-T2e：权限先行的混合工具检索与有界向量索引缓存。
继续E:/UAW/.worktrees/tool、dev/tool。干净后fetch tags、merge --ff-only ms-i2h-start，核对HEAD/tag commit，uv sync --frozen。读MS-I2h-parallel-packages.md第1/3/6节、DISPATCH和session/C；不读其他worker开发分支。
连续四项：1实际registry固定快照和当前role/权限/flags/provider先过滤；2显式embedding port的词法/向量召回和确定融合，返回现有DiscoveryResult让LLM选择；3绑定spec/provider/model/维度/规范版本的有界持久索引缓存、原子更新/失效/重启；4等待期间权限变化、取消/期限、跨用户泄漏、损坏/并发及原Tool回归。前两项交固定异步retriever/可选facade签名及SHA，再继续同包。
原小目录默认兼容，lexical-only显式配置；无实际embedding不生成hash/random向量充当语义，不静默冒充语义降级。结构化SQLite是可重建索引缓存，不是Tool注册/权限权威；最终仍复查当前ToolSpec/Access，不执行工具、不改用户固定模型。真实embedding adapter由A/管理员来源接线，受控数值测试只证明计算。
仅C允许目录；dot-source ops/start-dev-db.ps1 -Session C、alembic upgrade head，独立55434实跑受影响模块SQL和原结果回归。公共schema/依赖/flags先提案A，保留原失败与修复回执。源码/handoff分开提交，工作区干净交付，本包后停止。
```

## 发给D：MS-R2e

```text
开始UAW Session D完整能力包MS-R2e：已签名file.read的真实有界文件读取、OS身份复核和终态journal。
继续E:/UAW/.worktrees/runner、dev/runner。干净后fetch tags、merge --ff-only ms-i2h-start，核对HEAD/tag commit并uv sync --frozen。读MS-I2h-parallel-packages.md第1/4/6节、DISPATCH和session/D。
连续四项：1现有准入/RootBindings/独立owner与authority后，临时根内UTF-8常规文件读取（总1MiB/返回64KiB）；2打开后实际OS句柄最终路径、文件/根身份与替换竞争检查，关键await和提交前权限/取消/期限复查；3实际FileContent与设备签名journal、一次使用及重启恢复；4临时文件范围、Unicode/空/二进制、链接/越界/替换/同时编辑、撤销/过期/取消/并发与原D回归。前两项交ReadOnlyRunner固定构造/execute签名、依赖和SHA，继续同包。
只实现已有RunnerParametersFile.read，不新增list/IPC wire。authenticated_principal来自独立可信入口，不从command/body自证；无实际channel/owner/authority/签名拒绝，受控测试channel不是真实IPC。仅真实临时测试根，不碰用户文件；不安装/写入/exec、不改flags、不决定D03。随机OS测试凭据清理并保留回执，Runner ok不自动等于Tool业务成功。
只改D允许路径；需要SQL时自己的Session D库55435，不改其他库或A文件。公共缺口交A提案后继续独立项。阶段/最终源码与handoff分开提交，干净交付；本包后停止。
```

## A同时推进

A已完成MS-I2g/1077节点全量，下一步MS-I2h根实例/有限步单Agent循环；阶段接口到达即接线，worker自己实跑模块SQL。开发基线发布不是整个P1或真实LLM/IPC/exec已通过。

---

# 下一轮可直接转发：完整能力包

**2026-10-08 当前更新：下方MS-C5/MS-T2d/MS-R2d为已经执行的本轮派发原文。B/C/D三个最终组件均已接受，不再转发下方原任务让其重做。A已逐包合入并完成实际来源/装配验证，详见[MS-I2g-A1](../implementation/MS-I2g-A1.md)和[DISPATCH](DISPATCH.md)。MS-I2g全量回归运行中；下一轮完整范围见[MS-I2h能力包](requests/A/MS-I2h-parallel-packages.md)，固定基线发布后再开工。**

## 历史开工消息（保留）

日期：2026-10-08。B/C/D已向用户报告同步ms-i2f2且工作区干净。新包已准备，共同标签 **ms-i2g-start**；SHA见[DISPATCH](DISPATCH.md)。详细接口/目录/里程碑见[MS-I2g范围](requests/A/MS-I2g-parallel-packages.md)，实际产品进度见[进度说明](../implementation/PROGRESS-2026-10-08.md)。

## 发给B：MS-C5

```text
开始UAW Session B完整能力包MS-C5：通用Context登记、当前权威、来源读取到模型输入链。
继续E:/UAW/.worktrees/context、dev/context。工作区干净后git fetch origin --tags，再git merge --ff-only ms-i2g-start，核对HEAD与标签commit一致并uv sync --frozen。失败报告，不reset/rebase。
先读docs/coordination/requests/A/MS-I2g-parallel-packages.md第1/2/5/6节、docs/plan/sessions/B.md、DISPATCH。新registered.py/authority.py/readers.py归B；seed/intent、shared/schema、Model/Run/composition仍归A。签名和策略以详细范围为准，purpose使用已有agent_step。
连续完成四个里程碑：1可信登记、blob/命名SQL和CAS修订；2当前CompositionAuthority/Reader/规则来源；3build→固定snapshot→GenericModelInputs/引用完整链；4真实SQL重启/并发/撤销/原模块回归。前两项完成后提交阶段版接口、样例和SHA，再继续本包后两项，不等A最终合并才工作。
在自己的PowerShell执行 . ./ops/start-dev-db.ps1 -Session B，随后 .venv/Scripts/python.exe -m alembic upgrade head；独立端口55433。实跑B模块SQL并保存自身ignored回执，不复制A凭据，不修改其他库或共享evidence。
保持实际Run/固定模型/原文、当前权限与来源，材料不升格规则、缺非空工具验证源拒绝，缓存不跳过复查。只改B允许路径；公共缺口提案后继续独立项。最终源码/交接提交，工作区干净，报告接口、真实验证和A接线要求。P1整轮未因此接受。
```

## 发给C：MS-T2d

```text
开始UAW Session C完整能力包MS-T2d：只读工具调用编排、实际text.inspect adapter、持久结果和恢复来源。
继续E:/UAW/.worktrees/tool、dev/tool。工作区干净后fetch tags、git merge --ff-only ms-i2g-start，核对标签commit并uv sync --frozen；失败报告，不reset/rebase。
先读docs/coordination/requests/A/MS-I2g-parallel-packages.md第1/3/5/6节、docs/plan/sessions/C.md、DISPATCH。只改tool和C测试/requests/handoff，不依赖D开发分支，shared/schema/锁/composition/API归A。
连续完成四项：1审批/预算/账本到一次发送编排；2实际有界纯文本adapter及严格ProviderReceipt/原结果保存；3规范ToolResult、持久publish/Lookup/Reader并接原reconcile/outcome；4独立真实SQL的并发/重启/取消/响应丢失/费用恢复和原70项回归。前两项交阶段版接口/样例/SHA后继续本包，不等最终集成。
在本worktree . ./ops/start-dev-db.ps1 -Session C；独立端口55434，再运行锁定环境alembic upgrade head和C模块真实SQL。自身回执写ignored路径，不复制A配置或修改共享evidence/其他库。
缺executor发送前拒绝；approved/current resource检查保留，持久CAS重放不是发送权，未知不换attempt重发，不从Runner ok或HTTP200推断成功/零费用。text adapter不擅自加入产品目录，不开放flags、网络、本机文件、写入exec。最终源码/交接提交，报告真实结果和A接线缺口，完整MS-T2仍待整链验收。
```

## 发给D：MS-R2d

```text
开始UAW Session D完整能力包MS-R2d：实际OS控制密钥签名、授权根来源和适配器装配。
继续E:/UAW/.worktrees/runner、dev/runner。工作区干净后fetch tags、git merge --ff-only ms-i2g-start，核对标签commit并uv sync --frozen；失败报告，不reset/rebase。
先读docs/coordination/requests/A/MS-I2g-parallel-packages.md第1/4/5/6节、docs/plan/sessions/D.md、DISPATCH。只改D允许路径，消费现有RunnerCommandSigning/RunnerRoot/PrincipalMapping ports，不能从命令声明生成归属或授权。
连续四项：1独立control key绑定的签字/verify适配；2随机测试namespace内真实WindowsCredentialStore/ProtectedSigner验证并清理；3真实已消费选择/grant/期限/目录身份到opaque RootSnapshot；4装配例子与临时根、撤销/过期/主体/重启及原journal/admission回归。前两项提交阶段版接口、样例和SHA后继续本包后两项。
OS密钥不可用如实记录，原语fixture不当OS实连；不操作既有用户凭据或打印秘密。仅本机临时根，无真实选择/期限/owner映射拒绝。需要SQL时 . ./ops/start-dev-db.ps1 -Session D 使用独立端口55435；其他本机测试不必启动PG。
content固定Ref保留，不新增公共RefKind；不实现IPC/配对V2/真实文件动作、安装写入exec，不自行决定D03。公共提案交D requests；最终源码和handoff提交，报告实际回执、构造接线及仍缺真实来源。
```

## A同步推进

A执行MS-I2g：环境准备已经验证；并行审阅阶段版接口、处理公共提案和当前Run/政策/模型/认证来源接线。逐包接受而非等三包齐才开始；模块SQL由worker实跑，A重点做受影响模块和跨模块链路，全量在集成里程碑执行。

任务量按完整能力划分，不能保证固定耗时或完全消除依赖等待。A没有发送到其他聊天或改变worker工作区；将各自代码框转发即可，新包状态是已发布待开工，实际开工报告后再更新。
