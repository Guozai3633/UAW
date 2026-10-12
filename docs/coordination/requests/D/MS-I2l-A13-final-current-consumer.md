# A13 D M2：统一来源消费交付，原首次链仍未通过

2026-10-12。实际worktree E:/UAW/.worktrees/runner，分支dev/runner。
准确基线 ms-i2l-a13-source / 69fae72742a8a64b55a240cb735066aeef78240f；
远端正式发布元数据6ec7d0f5ea30d718efcdab29309f8c19c3436366已核对。
干净fetch、tag核对、ff、HEAD=tag、uv sync --frozen完成，不消费浮动integration。

| 交付 | 精确提交 |
| --- | --- |
| M1阶段源码 | bb24f69761429a110e5906063ed4333220f35f53 |
| M1检查点/参数/监控提案 | 2748a5524fd22722ad9aab13b831b0d07356e947 |
| 透明测量wrapper修复 | 68c665cf7baea2361b99ba8fb6805e8356384cfe |
| M2最终源码/测试 | 13ecd4bd44a896f51ec9c736eef0b4d6a8789be2 |

## 实际消费与效果顺序

current_source=None默认兼容旧调用。ReadOnlyHelper、HelperReadAssembly、ReadOnlyPipeEndpoint、
ReadOnlyRunner均显式传递原RunnerReadCurrentPort，Factory.create旧签名保持。
A13现有InstalledReadOnlyHelper在super之后已保存holder；D connect读取这个原对象，endpoint/runner要求同一实例。
A可在自己的installed super显式传current_source；D未修改A工厂/Run/SQL、公共workspace port、schema、锁或其它worker。
A同对象store/commands/authority/roots/registry绑定仍由其既有构造约束执行。

原first_byte owning边界固定until=min(first_byte+原pipe.timeout,session.monotonic_expiry)，
覆盖bootstrap.connected、receive、dispatch、execute/current及send；下游不再产生新now+10。
consumer拒绝bool/非有限值/过去或大于十秒的deadline，after-await实际时间与command/lease/root/channel较早期限仍复查。
reply到期在admission CAS和execution guard开始/结束及signed CAS本机guard内拒绝；不会因签名或数据库等待延期限。

完整current投影严格核对实际类型、固定Ref/hash、原登记命令/source/owner/actor/device/context/channel/key/root/actions，
复制脱离来源模型，AsyncAdmission.check逐字段比较原命令声明。它替换同点Reader→mapping→channel→root→旧authority递归展开，
不是旁加新current。独立NativeRootSource._read核验实际已消费native Ticket/选择签名/key/grant/目录身份，
admission.external保留真实命令签名/当前control key/root scope；本机await前后两次fresh composite，最终全投影比较。
原projected值仅比较固定声明，不跨等待作为allowed使用。

M2把设备原私钥持有检查移到第一次composite之前（仅检查自有key，不执行文件动作）。
新的admit_current在一次fresh回调内建立首次固定authority/channel，本机外部检查后再fresh，然后执行原admission CAS。
不在私钥await前后分别跑两个完整图；CAS后至execution claim前fresh current仍保留。
执行CAS、打开后/读后/sign/verify/publish后各关键等待的检查保持；OS实际句柄最终路径/根/文件身份、替换/编辑检测、UTF-8/1MiB/64KiB不变。
旧未注入分支保留既有完整AsyncAdmission入口。

recover/previous attempt继续独立Reader/数据权限/root/key/channel与原签名；不调用active composite。
cancelled Run不直接否认原可访问回执，未知/未签名attempt不新admit/reserve/dispatch/open或重发。
content Ref、Usage和billing_state不改；Runner ok不推Tool业务成功、零费用或not_applied。

## 回执与失败

所有原始XML/log/临时清理与成本保留在ignored tests/.artifacts/D/MS-I2l-A13。

| 回执 | 实际结果 | 范围 |
| --- | --- | --- |
| final-regression.xml/log | 233passed / 142.31s，0fail/error/skip | 原read_executor/AsyncAdmission/Windows读IPC/idle、37新composite/9deadline参数、原隐藏helper实际一次open/并发/重启签名journal恢复 |
| sql-boundaries.xml/log | 10passed / 225.30s，0fail/error/skip | 实际SQL/Web/Windows双key/双进程，等待后root/key/stop/角色/Run cancel/policy/期限/owner/config/provider拒绝，command/open0 |
| stage.xml/log | 180passed / 72.31s | M1兼容，已包含于最终并集，不重复计数 |
| composite-stage-final.xml/log | 25passed / 6.71s | M1组件投影，包含于最终37，不重复计数 |
| effects.xml/log | 127passed / 68.37s | 签名后变化/取消/CAS期限，包含于最终并集 |
| m2-order.xml/log | 37passed / 16.63s | 准入效果排序后的新组件，包含于最终并集 |
| lifecycle.xml/log | 7passed / 43.53s | 原双进程helper/恢复/并发，包含于最终并集 |
| chain.xml/log | 1failed / 41.82s | command1/open0；D透明receive wrapper不接受deadline，child TypeError；已修，失败保留 |
| chain-2.xml/log | 1failed / 51.51s | command1/open0；5composite共8.363s、同绝对deadline，原回复取消 |
| chain-3.xml/log | 1failed / 74.16s | M2排序后command1/open0；4composite共7.954s、同绝对deadline，原回复取消 |

最终去重243个不同节点通过，accepted-nodes.json精确列节点；不是全量或产品接受。
原成功期望test_a8_file_facade_approval_budget_actual_helper_read断言没有放宽/xfail/skip；完整首次读仍失败。
chain-2/3实际admission各1，file_read_attempts各0，无receipt journal，不从admission签发假回执。
该完整链的signed journal恢复/原文件变化保持快照/零新发送或打开断言尚未到达，不能报通过。
独立真实临时OS/Ed25519/SQLite/双进程组件证明实际一次open、原快照/签名journal与重启恢复，其authority/native登记为明确fixture。

初始化测试失败全部保留：composite/composite-2各25fixture注册error；composite-3有25严格JSON模型构造failure；
composite-4有10fixture冻结模型/行动范围failure及15pass；composite-final有1deadline错误语义failure及24pass。
均修复后覆盖最终通过节点，不隐去原错误。stage-mypy.log17个初始类型错误保留，后续35D源码Mypy通过。
Ruff通过、38文件格式通过、git diff --check通过；8份A/公共/锁文件规范化摘要与准确基线一致。
没有重跑旧695或汇合全量。

主要验证命令（其余分阶段准确命令见本次工具回执与XML）：

```
. ./ops/start-dev-db.ps1 -Session D
.venv/Scripts/python -m alembic upgrade head
.venv/Scripts/python -m pytest tests/integration/runner/test_read_executor.py tests/unit/runner/test_async_admission.py tests/integration/runner/test_windows_read_ipc.py tests/unit/runner/test_pipe_idle.py tests/integration/runner/test_composite_read_current.py tests/unit/runner/test_composite_endpoint.py tests/integration/runner/test_original_journal_recovery.py tests/integration/runner/test_helper_idle.py tests/integration/runner/test_helper_runtime.py::test_real_hidden_helper_native_once_read_reconnect_recover_restart tests/integration/runner/test_helper_runtime.py::test_two_hidden_helpers_concurrent_once_journal_no_new_read_on_recover --basetemp=tests/.artifacts/D/MS-I2l-A13/final-regression-temp --junitxml=tests/.artifacts/D/MS-I2l-A13/final-regression.xml -q
.venv/Scripts/python -m pytest tests/integration/runner/test_installed_file_boundaries.py --require-postgres --basetemp=tests/.artifacts/D/MS-I2l-A13/sql-boundaries-temp --junitxml=tests/.artifacts/D/MS-I2l-A13/sql-boundaries.xml -q
.venv/Scripts/python -m pytest tests/integration/runner/test_installed_file_chain.py --require-postgres --basetemp=tests/.artifacts/D/MS-I2l-A13/chain-3-temp --junitxml=tests/.artifacts/D/MS-I2l-A13/chain-3.xml -q
$env:MYPYPATH='src;apps/local_runner'
.venv/Scripts/python -m mypy apps/local_runner/uaw_runner src/uaw/workspace
```

## 实际来源成本/清理

source-costs.json按每实例保存阶段/操作/GET次数与累计耗时、reply deadline、command/open及清理。
最后原链ready23.343s，assembly0.524s，审批2.670s，受控决定1.422s，批准后42.218s，cleanup0.684s。
child endpoint9.028s、runner execute8.445s、2个runner.current共8.052s、4个composite共7.954s；
原session_current累计165次/18.844s包括bootstrap/native与read，不可当纯10秒执行段成本。
旧authority.current调用未出现，未把完整authority与composite两图叠加。
四个composite的deadline完全相同（具体浮点值只保存在本地指标），没有重新增加十秒。
这里reply边界提前终止；OS open/signed publish/recovery未进入，不能记作零成本或成功。

十个SQL边界ready14.621–22.262s，等待后拒绝0.015–0.588s。
父端GET789–986次/2.224–3.497s，child3712次/5.604–9.541s。
多个D测试批次并行、有机器负载差异；GET累计嵌套/并发，不与墙钟相加，也不计put/事务。
不是同口径独占生产性能对比，不因某批较快声称通用预算达标。

13个installed临时实例（含三个首次链失败）各核对4随机凭据不存在、2角色key撤销、child退出和proof pipe关闭。
38份独立Windows IPC随机namespace报告均cleaned=true；无自有helper/pytest Python进程残留。
D55435保持ready，未truncate其它库、操作既有用户凭据或关闭他人进程。

## A输入/停止点

M1检查点和构造见MS-I2l-A13-stage-current-consumer.md；watch提案覆盖仍适用。
A拟新增SQL-only wait_changed尚未在本固定源发布，D未消费浮动源码。
目前D完整session.check监控保留；不能以SQL-only changed代替双方实际当前账号/设备/owner会话/enrollment/candidate/native证据登记。
A需明确peer失效SQL来源和原immutable peer/public key/OS/channel对应关系，D保留真实native SQLite/grant/Ticket/双方key/OS/live pipe检查。
缺覆盖时继续pending，不以测试Event/更长sleep、删检查或延期限换通过。
A13生产checked_metadata默认False保持；没有擅自打开输入优化或flags。

需要A继续有界生产来源与响应成本接线，并发布准确源后再验证原首次链与原journal。
实际SQL执行中lease/fence变化尚未达到打开阶段；D组件对lease/fence/两角色key/owner/channel/root/签名后/协作取消/CAS期限有覆盖，不能冒充生产整链。
真实：SQL/Web身份、Windows双keys/ACL/OS实例/双进程和独立临时OS/签名/SQLite。
受控：临时native typed选择、原SQL审批决定、新Run初始model/provider/availability/flags、组件authority/channel/composite fixture。
待真人：无新本人窗口、无代点击批准/接受、无用户目录/正文或模型调用。
保持只读、原10秒回复/30秒lease/120秒root及其它更早期限，写入/安装exec与flags关闭。
本续项D组件/接口交付，完整首次链和监控覆盖pending，不自动扩包或同步下一浮动来源。
