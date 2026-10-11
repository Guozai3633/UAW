# A9 D 定向修复：独立项交付，首次实链待 A 来源

2026-10-11；dev/runner，E:/UAW/.worktrees/runner。
实际基线 ms-i2l-a9-journal-source / 225f5006f9ad246fb17816363beda4f1f1445876；
固定任务文档 ms-i2l-a9-journal / 22bfb00954a061a48fc3f6143593e2e91bd2c6a7。
远端及正式DISPATCH核对、干净快进和uv sync --frozen已完成，保留全部旧D历史。
阶段源码7395eb7fc32c3e99b46840f3432358fee38da170；
阶段接口55a65e7d1c940cc3032ef9787d82a5519b135f73；
实际来源拒绝提案9a7574fac4b096a6d79242d125530ac3467fef79；
最终源码79261603c5a045c576410bf3c5cc21b2af11d719。

## 修改与边界

- runtime.HelperReadAssembly仅构造固定依赖，以原registry私有snapshot校验元数据，不在构造时展开权限链。endpoint随后复查session，execute独立复查Reader/owner/channel/root/authority。
- ReadOnlyRunner删除私钥await后、紧接完整AsyncAdmission前的重复current。保留第一次固定比较、完整两次准入权威、外部key/root、admission后比较、执行CAS、实际OS句柄、read/sign/verify/publish后检查与原journal恢复。
- D测试增加10个私钥await后拒绝节点；A9实际审批资源Reader的等待注入点；实际账号/配置/provider变化；原成功期望节点追加已发布signed journal恢复及原文件修改后快照不变/command1/open1断言（该完整节点尚未通过）。
- 子进程指标记录checkpoint调用次数/累计秒数/失败码和GET成本；原子替换JSON修复观察指标竞态。指标不是权限、正文或proof，未加入运行许可缓存。

公开Runner/execute/Factory签名保持。watch现有完整session检查仍保留。
有界current及wait_changed提案待A owning实现，见MS-I2l-A9-stage-read-budget.md；未私自装配测试Event或新增公共schema/RefKind。
原10秒frame/response、15秒普通/90秒首次、120秒root、30秒lease和较早源期限不变。
未改A控制端/shared/锁/composition/HTTP或其它worker。7个公共/A源码与锁的规范化摘要相对准确基线未变。

## 验证（原始回执均保留）

回执目录 ignored tests/.artifacts/D/MS-I2l-A9；accepted-nodes.json精确列195个不同节点。
最终接受覆盖以D实际通过为依据，不是A产品接受或一次全通过。

| 回执 | 实际结果/耗时 | 范围 |
| --- | --- | --- |
| stage.xml/log | 173 passed / 113.49s | read_executor、AsyncAdmission、真实Windows读IPC；新增私钥await变化拒绝 |
| lifecycle.xml/log | 12 passed / 47.91s | 隐藏双进程helper、真实OS钥匙/pipe、原签名恢复/文件变化/一次open、断帧/超长/取消/期限 |
| final-boundaries.xml/log | 9 passed、1 failed / 419.22s | 十个实际SQL/Web/Windows临时实例的等待后来源；control_key指标JSON竞态失败保留 |
| metadata-fix.xml/log | 1 passed、9 deselected / 42.57s | 原子指标修复后同一control_key实际拒绝复跑 |
| baseline.xml/log | 1 failed / 83.44s | 准确A9原成功期望：ipc_broken、command1/open0 |
| stage-chain.xml/log | 1 failed / 89.83s | D阶段后仍ipc_broken、command1/open0；首次current/root处enrolled_actor_denied |
| new-boundaries.xml/log | 3 failed / 179.63s | 旧bridge等待点未到达；修为A9真实审批前资源Reader，旧失败保留 |
| original-boundaries.xml/log | 7 failed / 422.92s | 同一旧注入点批次；全部清理，最终十项在实际Reader重验 |

最终去重173+12+9+1=195，覆盖节点无失败/错误/跳过；原完整首次文件链仍失败。
没有重跑旧695全量。13个原始failure节点保留（包含两个原链失败和测试诊断失败），不以跳过/xfail遮蔽。
Ruff通过、38文件格式通过、Mypy34个D源码通过，git diff --check通过。

命令（D独立环境）：

```
. ./ops/start-dev-db.ps1 -Session D
.venv/Scripts/python -m alembic upgrade head
.venv/Scripts/python -m pytest tests/integration/runner/test_read_executor.py tests/unit/runner/test_async_admission.py tests/integration/runner/test_windows_read_ipc.py --basetemp=tests/.artifacts/D/MS-I2l-A9/stage-temp --junitxml=tests/.artifacts/D/MS-I2l-A9/stage.xml -q
.venv/Scripts/python -m pytest tests/integration/runner/test_original_journal_recovery.py tests/integration/runner/test_helper_idle.py tests/unit/runner/test_pipe_idle.py --basetemp=tests/.artifacts/D/MS-I2l-A9/lifecycle-temp --junitxml=tests/.artifacts/D/MS-I2l-A9/lifecycle.xml -q
.venv/Scripts/python -m pytest tests/integration/runner/test_installed_file_boundaries.py --require-postgres --basetemp=tests/.artifacts/D/MS-I2l-A9/final-boundaries-temp --junitxml=tests/.artifacts/D/MS-I2l-A9/final-boundaries.xml -q
.venv/Scripts/python -m pytest tests/integration/runner/test_installed_file_boundaries.py -k control_key --require-postgres --basetemp=tests/.artifacts/D/MS-I2l-A9/metadata-fix-temp --junitxml=tests/.artifacts/D/MS-I2l-A9/metadata-fix.xml -q
.venv/Scripts/python -m pytest tests/integration/runner/test_installed_file_chain.py --require-postgres --basetemp=tests/.artifacts/D/MS-I2l-A9/stage-chain-temp --junitxml=tests/.artifacts/D/MS-I2l-A9/stage-chain.xml -q
$env:MYPYPATH='src;apps/local_runner'
.venv/Scripts/python -m mypy apps/local_runner/uaw_runner src/uaw/workspace
```

## 实际成本与清理

costs-current.json逐实例保存每阶段实际耗时、GET次数/累计秒数、command/open和清理。
阶段原链：ready32.063s、assembly0.699s、审批2.813s、受控决定1.359s、批准后46.596s、cleanup1.077s。
reserve0.046s、dispatch0.038s、lease0.063s、command register7.099s、collect3.320s、pipe4.333s。
child endpoint2.606s、runner execute1.512s、首次current0.886s、root source0.023s；
均在enrolled_actor_denied处停止，authority/recovery未进入，不能记作零成本或成功。
SQL边界原十项ready32.916–35.105s、assembly0.728–0.788s，等待后拒绝0.020–1.134s。
父端GET933–1132次/4.572–5.627s；child3712次/11.804–12.990s。
受影响control_key复跑另见对应metadata。GET累计是嵌套/并发测量，不能与墙钟求和。
有两个独立边界测试批次并行，不能视作独占SQL生产性能基准。put/事务成本不包含在GET累计内。

23个installed临时实例（含所有失败）各验证4随机凭据不存在、2当前角色key撤销、child退出和proof pipe关闭。
17份独立Windows IPC随机namespace清理报告均cleaned=true；所有自有helper/pytest Python进程无残留。
D55435保持ready，没有truncate其它库、操作既有用户凭据或杀其它进程。

## A 接线与未通过项

1. 当前准确源将EnrolledPeerRegistry同时注入NativeRootSource.mapping；RootSource.current原契约查询ctx.principal用户，实际mapping仅接受两个peer actor，首次根查询返回enrolled_actor_denied。详见MS-I2l-A9-owner-root-source.md。A需提供真实账号会话/当前enrollment/双key/OS/channel/device关系校验的owner适配，不得复制ctx或body为授权。D保留拒绝。
2. A owning bounded recheck/wait_changed按阶段提案读取原完整绑定、当前角色/审批/配置/provider/Run/预算/lease/fence/Root/device/key/channel。缺生产来源仍不装配；D不能改A公共契约或控制服务。现有watch不能因成本问题删关键检查。
3. A发布准确修复源后复跑原首次成功期望及原published journal恢复；实际一次OS open、原签名/快照、零新command/open尚未在A原完整链证明。A补的6个SQL/SQLite/签名组件不代替这个门槛。
4. 执行中真实SQL lease/fence变化的正向接入测试未达到打开阶段；D独立临时OS/真实签名组件对lease/fence/期限/取消和after-sign来源变化有覆盖，不能冒充A生产链。

真实：SQL/Web身份、Windows密钥持有/ACL/OS实例/双进程、临时根OS读取与SQLite/真实Ed25519。
受控：临时namespace的native typed选择、初始新Run模型/provider/availability/flags与审批决定、D组件authority/channel登记。
待真人：未新弹窗、未代点击确认/接受、未读用户目录/用户正文、无新模型调用。
Runner ok不推Tool业务成功；未知结果不重发，不推零费用或not_applied。
本次交付仅D可独立修复/验证；首次原完整链、有界生产来源与本人验收仍pending，原本轮继续，不进入新共同包。
