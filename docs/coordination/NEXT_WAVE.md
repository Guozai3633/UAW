# 下一轮可直接转发：完整能力包

**2026-10-08 当前更新：下方MS-C5/MS-T2d/MS-R2d为已经执行的本轮派发原文。B继续MS-C5后半段；C/D最终组件已接受，不再转发原任务让其重做。A已逐包合入并完成实际来源/装配验证，详见[MS-I2g-A1](../implementation/MS-I2g-A1.md)和[DISPATCH](DISPATCH.md)。开发中的B保持ms-i2g-start，下一包另列清楚依赖和目录后再开工。**

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
