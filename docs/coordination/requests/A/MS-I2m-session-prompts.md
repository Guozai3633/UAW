# MS-I2m：四个会话的开工提示词

共同固定标签ms-i2m-start；准确40位SHA在正式发布后置于本页页首及远端DISPATCH。这里的包名是本轮明确分工；四里程碑连续开发，不在M1后自动等待新派发。

## A / MS-I2m

```text
开始UAW Session A MS-I2m，继续E:/UAW / integration。先fetch核对远端DISPATCH正式发布的ms-i2m-start准确SHA和tag一致；在自己已发布HEAD继续，不回退到worker基线。
读取docs/coordination/requests/A/MS-I2m-AD-contract.md、MS-I2m-parallel-packages.md第1/2/3/7/8节、DISPATCH及docs/plan/sessions/A.md。
连续M1–M4：1当前Run对话读图/具体问题/回执、真实Idle账本adapter、0.2认证与CAS/幂等控制事务，先发阶段SHA。2同Run回答/纠正在安全边界生效、租约/原效果对账、接D时钟与剩余主动段，旧调用和授权deadline不变；公布准确新服务供B联调。3实际固定用户模型问答/纠正及办公学术粘贴成果、准确引用/逐项核验/用户接受，按C契约导出全部实际尝试/失败/费用。4逐包接受后跨模块和一次汇合全量，固定H02启动给本人体验。
只改A保留范围；B前端、C评测、D execution_clock及其测试由原worker修改。阶段到即审，业务错误交原worker，不代同步或改写分支。保留H01-v5运行快照/原用户历史与所有失败/pending费用。固定用户模型，运行时子Agent/DAG/本机写入安装exec关闭，不代本人发送确认或接受；未知效果先对账不重发。
```

## B / MS-U4（前端）

```text
开始UAW Session B MS-U4。沿用E:/UAW/.worktrees/context、dev/context，先检查干净、fetch origin --tags，用git show origin/integration:docs/coordination/DISPATCH.md读取本轮正式40位SHA，核对ms-i2m-start^{commit}，只git merge --ff-only ms-i2m-start，不合浮动integration。非快进保留现场，不reset/rebase/stash；原提交/handoff保留。同步独立锁环境。
读MS-I2m-AD-contract.md、MS-I2m-parallel-packages.md第1/2/4/7/8节、DISPATCH和session/B。只改apps/web及本轮B文档/回执，暂停Context。
连续M1–M4：1五个精确0.2控制端点和RunConversationView，问题从原持久ID发现，不猜最后消息；先交typed消费例和阶段SHA。2原Run回答、运行中纠正、accepted/applied/superseded/cancelled反馈和草稿，普通消息与成果接受分清。3刷新/丢响应同request_id查询、两页CAS/取消/旧协议/失效认证，防自动重发和重复Run。4A准确新服务到达即联调，受控fixtures不冒充实际来源；原本人会话只读，不代本人发送/确认/接受。交冻结安装/类型/构建/相关单元与Playwright、dist hash及独立handoff。
M1/M2阶段SHA到即交A，继续本包后续；生产源未到只把实际联调记pending，不等它才写页面。保留旧失败/费用/记录，不改公共schema/后端/锁/flags；包后停止，不自动扩包。
```

## C / MS-E1（独立质量评测，本轮临时新职责）

```text
开始UAW Session C MS-E1。沿用E:/UAW/.worktrees/tool、dev/tool，干净检查→fetch origin --tags→git show origin/integration:docs/coordination/DISPATCH.md核对本轮正式准确SHA及ms-i2m-start^{commit}→只git merge --ff-only ms-i2m-start→独立锁环境。非快进保留现场，不reset/rebase/stash；原Tool提交/handoff保留。
读MS-I2m-AD-contract.md第1/4/5节、MS-I2m-parallel-packages.md第1/2/5/7/8节、DISPATCH、session/C和support-evaluation设计/H01-I02/I03。临时归属仅新src/uaw/evaluation/、ops/evaluate_conversation.py、tests/unit/evaluation/和fixtures/evaluation/及本轮C质量文档/回执；不改原Tool/Runner/Run/共享契约或锁。
连续M1–M4：1固定离线CLI与严格suite/manifest/observation/review/report schema和可运行例，阶段SHA到即交A。2做12–20条办公/学术/技术/必要澄清/合理歧义/纠正保留要求的候选样本和反例，一手资料实际查证，未人工核对标needs_human_review。3独立计算答案错误、Reviewer漏判或N/A、无谓阻断/缺证据执行及完整失败重试/时间/费用，缺样本/错hash/未审关键项不能passed，字符串只筛查不充当事实判定。4消费A实际候选/基线与完整用量做离线比较；未到记真实实测pending，交确定性命令/schema/失败历史/最终源码和独立handoff。
不发真实LLM、不读A凭据/本人会话、不重放写操作，不新增依赖；本包无数据库需求记N/A。M1/M2后继续余下本包，结束干净停止；不把受控结果或AI审阅冒充人工质量通过。
```

## D / MS-K1（主动/等待计时，本轮临时新职责）

```text
开始UAW Session D MS-K1。沿用E:/UAW/.worktrees/runner、dev/runner，检查干净→fetch origin --tags→git show origin/integration:docs/coordination/DISPATCH.md核对本轮正式准确SHA与ms-i2m-start^{commit}→只git merge --ff-only ms-i2m-start→独立锁环境；非快进保留现场，不reset/rebase/stash，原Runner提交/handoff/失败不动。
读MS-I2m-AD-contract.md尤其第3节及src/uaw/run/clock_ports.py、MS-I2m-parallel-packages.md第1/2/6/7/8节、DISPATCH和session/D。本包仅新增src/uaw/run/execution_clock.py、tests/unit/run_clock/、tests/integration/run_clock/及D文档/回执，不改原Runner、clock_ports、共享DTO、其他Run/预算/队列代码。
连续M1–M4：1ExecutionClocks(records,必需effects,可信now)与current/change固定入口、纯主动/等待计量，阶段SHA和例到即交A。2原owner/Run/binding/clock/具体问题复核、CAS和clock+binding.clock_ref同tx写；pause必须真实Idle检查，无依赖不能准许。3自己55435实跑并发/重启/回滚/长等待/时间倒退/超额/取消/unknown和原调用/审批/root期限不变。4接A真实Idle阶段适配验证消费，缺完整生产链准确pending，交不同节点回执/失败历史/构造消费例/最终源码及独立handoff。
change不得commit/另开事务/改Run或input_revision/completion_mode/预算/调用期限/权限，也不唤醒执行；stopped不可复活，等待不重领全额，未知效果不免费暂停。A负责剩余主动段新调用准入和完整续跑；你不代写A接线、不打开native窗口/flags、不代本人确认。M1/M2交阶段后继续本包，结束干净停止。
```
