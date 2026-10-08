# 下一轮可直接转发：MS-I2h

日期2026-10-08。B/MS-C5、C/MS-T2d、D/MS-R2d三个最终组件已接受；A在B最终合入后2条实际组装复验通过。新包共同固定开发基线 **ms-i2h-start**（实际SHA见[DISPATCH](DISPATCH.md)；git rev-parse标签核对）。完整MS-I2g/1077节点回归由A继续，新包可以同时开发。旧任务下移为历史记录，不再重做。

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

A继续MS-I2g完整回归和发布验收结果，随后进入MS-I2h根实例/有限步单Agent循环；阶段接口到达即接线，worker自己实跑模块SQL。开发基线发布不是整个P1或真实LLM/IPC/exec已通过。

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
