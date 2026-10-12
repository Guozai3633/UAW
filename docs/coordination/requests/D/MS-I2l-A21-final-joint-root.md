# A21 D 最终：联合 native 根/原审批消费与首次链回执

## 结果与准确版本

组件交付完成；**原首次完整读取仍未通过**，不得提升为完整MS-R2、Tool成果或本人接受。
实际 E:/UAW/.worktrees/runner / dev/runner，原HEAD9a419a943e3c385f4a4beb532fdb25dbe05be991干净。
fetch tags、远端准确tag及origin/integration DISPATCH均核对：
**ms-i2l-a21-source / 88e7078cc0b7aee66136ebd44ec0d057e184b209**，仅快进固定tag，HEAD精确等于source，
uv sync --frozen（64包）；没有浮动integration/reset/rebase/stash或覆盖公共文件。

- M1源码 **3a2e145a08043686837ac7d2e43d2317e5ec53f2**，独立阶段说明1f55eb701e0546ed2f0b781f11abdbcee6e17df8。
- 最终/M2源码 **7157883c5917c2f8127092ae6e6ecbc8e116d413**，独立阶段测量说明7de5410176aa02dbb1831fd63bf266d267e04140。
- 原A15/A20源码、handoff、失败及清理口径修正全部保留。独立最终handoff追加原D.md后停止。

## 文件与内部接口

源码仅 apps/local_runner/uaw_runner/root_source.py；D测试 test_checked_native_root.py、
test_installed_joint_root.py、installed_file_child.py；D requests阶段/最终说明，最后独立D handoff。
不改A/shared/workspace/contracts/schema/锁/HTTP/composition/其他worker；12公共/A/锁归一化摘要不变。

原 NativeRootSource 构造无需新参数：

```python
root = await roots.checked_current(device_id, workspace_ref, original_ctx, check=metadata_check)
# metadata_check: Callable[[JsonObject], Awaitable[None]]
```

A现有 OriginalFileApprovalGate.check_root、InstalledToolApprovalGate.check_root及RunnerCommands发现即可使用。
同一个实际拥有源执行：原owner→完整_read→detached完整root→await callback恰好一次→原owner→完整_read→
完整owner/root比较与新时钟→后root。legacy current调用同核心但无callback，原验证保留。
_read继续验证真实已消费SQLite Ticket/grant/hash/native期限、当前device key角色及撤销、真实Ed25519
selection签名、实际目录/OS身份/scope及最终重新读取。绝对路径留本机，无公开RefKind/DTO/wire变化。

首_read返回时root已过期立即拒绝不进callback；callback以后重新取时钟与owner/全部根证明。
输入嵌套变更、原ctx/workspace腐坏、完整revision变化拒绝；noncallable/非None返回拒绝，
非awaitable、异常/取消/TimeoutError原样传播；不fallback、不缓存allowed、不执行/确认/模型调用。
callback仅原SQL元数据审批，不能用它授执行许可。原效果前后fresh检查/一次CAS/真实OS句柄复核不删减。

## 实际验证和去重

最终通过覆盖**265不同D节点**，0最终组件failure/error/skip。不是一次全量，也不合计A节点：

| 回执 | 实际通过 | pytest显示耗时 | 口径 |
| --- | --- | --- | --- |
| native-final.xml | 85 | 32.55秒 | 33新增联合边界＋52原native根 |
| regression.xml | 207 | 142.95秒 | 包含35联合边界；async admission、真实receipt、Windows只读IPC、原journal重启恢复、helper/window/endpoint |
| boundary-final.xml | 36 | 10.13秒 | 最终边界，含callback开始前root到期，不与上表重复多计 |
| joint.xml | 2 | 70.43秒 | 实际installed两Gate测量及取消/较早超时/native撤销 |
| sources.xml | 3 | 86.54秒 | 实际provider/approval/account SQL来源变化，两Gate拒绝 |

精确JUnit秒与逐节点索引：ignored tests/.artifacts/D/MS-I2l-A21/component-validation.json、accepted-nodes.json。
Ruff/4文件格式通过；Mypy36 D/workspace源码通过；git diff --check通过。
首轮native.xml 83通过/2测试准备失败：对冻结DTO赋值触发Pydantic，改为明确对抗性内存腐坏；
原格式/类型失败日志及标准库取消诊断保留。无删检查/跳过/延时，不重跑旧695。

真实SQLite/Ed25519/native临时目录组件的owner/native为明确fixture；实际installed五个metadata实例
使用真实Web/SQL当前enrollment/native-account journal/双方protected proofs/OS双key/双进程IPC，
native输入、approve_once/provider及新Run可用flags仍为明确受控fixture；不是本人点击或真实模型。
两Gate类在parent同图测量；原首次链另外实际消费隐藏child的原Gate，不能用parent测量假称child执行通过。

## 同图查询测量

完整root及审批结果一致，共享authority/resources对象保持原样：

| Gate / 路径 | root _read | owner | owning enrollment | SQL SELECT | A角色OS | 当前目录key | 单次秒 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| control legacy | 4 | 4 | 4 | 276 | 32 | 56 | 1.9838584 |
| control joint | 2 | 2 | 2 | 244 | 16 | 28 | 1.5453325 |
| child类 parent图 legacy | 4 | 4 | 4 | 276 | 32 | 56 | 1.4539610 |
| child类 parent图 joint | 2 | 2 | 2 | 244 | 16 | 28 | 1.4293121 |

SQL只数await owning Task中的uaw_records SELECT；root包含完整SQLite/proof/OS身份读取；
OS只数A enrollment角色观察，不含独立pipe及local根身份检查，后者保留。
每个剩余图的完整OS/key/root检查不变，减少的是原重复两组括号。无current缓存；单样本不报生产加速比例。
实际role/provider/approval/account变化均拒绝，新root撤销、取消、较早超时拒绝，metadata command0/open0。

## 原首次链：仅一次失败，未重发

原 test_installed_file_chain.py --require-postgres 全部成功断言未改，独立运行一次：
**1 failed / 89.37秒**，结果failed/invocation_interrupted，原result.kind==ok断言失败。
实际 **command1/open0，admission1/claim0/signed0/publishedRef0/terminal_receipts0**。
SQLite直接核实，未知命令不重发；无真实签名终态所以原链的FileContent/content Ref及改文件后恢复未达到。
不能从admission造receipt，不推not_applied/零费用。原D组件的真实签名journal恢复本轮已通过。

真实child的联合root Gate/source各7次约7.1341/7.1315秒，其中1次CancelledError；
4次composite current和1次SQL wait_changed共用同一原first-byte绝对reply deadline。
执行准入完成后fresh current尚未完成，claim前停止；endpoint watch报告ipc_identity_denied，
父端原10秒交换结束关闭后取消子任务，不能说是用户撤销或root证明无效。
诊断只支持这一层停止点，不能把聚合耗时误认成最后一个内部SQL节点的精确栈。

| 实际阶段/来源 | 次数/耗时 |
| --- | --- |
| parent setup / ready / assembly | 1.2454 / 29.6471 / 0.5670秒 |
| approval query / 受控SQL决定 | 3.0523 / 1.3611秒 |
| approved facade → unresolved结果 | 47.7842秒 |
| reserve / dispatch / lease acquire | 各1；0.0547 / 0.0397 / 0.0565秒 |
| bridge source / collect / register | 2/4.9013秒；1/2.1639秒；1/4.6570秒 |
| 原signed pipe交换 | 1/10.0260秒 |
| child factory / callback-ready | 3.5504 / 17.9678秒 |
| child paired registration / single / owning | 118/11.8775秒；43/2.7023秒；253/11.0826秒，无pair fallback错误 |
| child owner mapping / registered Reader | 92/6.7423秒；3/1.8757秒 |
| child joint Gate / joint NativeRootSource | 各7；7.1341 / 7.1315秒，包含1次取消 |
| child composite / execute / current | 4/9.6384秒；1/7.3026秒；2/6.5738秒，末次取消 |
| child local connection / SQL watch | 84/4.0444秒；1/7.9734秒 |
| fresh SQL witness/poll | 63/1.3614秒 |
| parent GET累计 / child GET累计 | 7108/28.6732秒；4739/15.3129秒 |
| cleanup | 1.5514秒 |

均为实际await/查询累计计时，嵌套与monitor并行不可相加成墙钟；GET包括启动/空闲等待/读取整个生命周期。
child signatures=2是native启动签名，非execution receipt。原frame=command只有一次。
Python3.14 asyncio shield取消后主动记录IPC worker的ipc_broken错误（标准库_log_on_exception语义）；
原日志保留，没有屏蔽或冒称成功，实际CancelIo/关闭/随机凭据/子进程清理已核实。
精确原metadata/query/phase/diagnostic/SQLite及chain-summary.json全部留ignored artifact目录。

## A下一步输入与清理/停止

1. D已完整消费A实际checked_current能力，不缺新公开接口或装配参数。
2. 原预算内root/Tool/current共同图仍未完成。每次实际Gate joint sample仍244 owning-task SQL SELECT；
   请A定位其原审批/Run/model/provider/config/权限/预算/lease/owner共同图重复展开，提供准确同次拥有来源接口
   和成本边界后再消费。保持完整前后fresh/current/root/key/OS验证，不能以fast peer/unchanged SQL授许可。
3. A原control登记/发送与Reader/actor/current/lease期限归A；D不私改A图、增加reply时间、删除检查或flags。
   未签名unknown保持不可用。新的实际整链成功之前，材料→固定用户模型→准确引用/核验/本人接受仍pending。

本轮6个独立installed实例（5 metadata＋1原链）各4随机OS凭据不存在/2role keys撤销/child退出/proof pipe关闭；
19份Windows IPC namespace报告cleaned=true，CIM确认无本轮自有helper/pytest残留，按物理路径去重pytest current别名。
仅自己D55435库/临时根，未操作用户凭据/项目/其他session库/进程；旧A15/A20清理回执不覆盖。
保留原10秒reply、15/90秒启动、30秒lease、120秒root及更早期限；原文/固定用户模型/权限/版本/CAS保持。
flags/checked_metadata/子Agent/DAG/写入安装exec关闭，不代D01/D03/D06。本人确认pending。
最终说明与独立handoff提交后工作区干净，本续项停止，不自动同步下一源或扩包。

```powershell
. ./ops/start-dev-db.ps1 -Session D
$env:MYPYPATH='src;apps/local_runner'
.venv/Scripts/python -m mypy apps/local_runner/uaw_runner src/uaw/workspace
.venv/Scripts/python -m pytest tests/integration/runner/test_checked_native_root.py tests/integration/runner/test_native_root_source.py -q
.venv/Scripts/python -m pytest tests/integration/runner/test_installed_joint_root.py --require-postgres -q
.venv/Scripts/python -m pytest tests/integration/runner/test_installed_file_chain.py --require-postgres -q
```

207回归命令：python -m pytest tests/integration/runner/test_checked_native_root.py
 tests/unit/runner/test_async_admission.py tests/unit/runner/test_receipts.py
 tests/integration/runner/test_original_journal_recovery.py tests/integration/runner/test_windows_read_ipc.py
 tests/integration/runner/test_helper_root_windows.py tests/unit/runner/test_composite_endpoint.py -q。
各命令均独立 --basetemp=tests/.artifacts/D/MS-I2l-A21/对应-temp，JUnit与原失败日志保留；
命令样例不构成新的自动运行授权，也不是一次265全量通过回执。
