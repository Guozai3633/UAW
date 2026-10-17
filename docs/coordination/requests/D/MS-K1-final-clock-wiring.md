# MS-K1 最终组件交接：ExecutionClocks

2026-10-17，E:/UAW/.worktrees/runner / dev/runner。
本包组件交付；严格跨原墙钟的A6续跑仍失败，**不宣称完整长等待/H02或生产安装通过**。

## 版本、归属和提交

原HEAD317549c1d0add6e1a2efa6d5ffda7283e9b40dda干净，git worktree list确认原runner路径。
fetch origin --tags、git show origin/integration:docs/coordination/DISPATCH.md与ls-remote准确核对：
先ff ms-i2m-start / **1f84a746cfbd2ceeab15876f9260a1d2c74d6cfe**，再ff
ms-i2m-a6-source / **b16c69a92d81124c00fb859ce8123748f56df054**，各HEAD准确，uv sync --frozen 64包。
A6-wiring是源码tag后的正式metadata，从origin/integration只读消费；没有合浮动分支。

- M1/M2源码 **81d8f9989fc5825c531f9c568cf7898b1252a841**；阶段说明 **aae77f0c0e8190677a0af9bd63f9972422f6f896**。
- 最终运行源码 **3f58011e0a8464b8a8d90b63b2d046a6a061c344**；M3阶段 **586f3e5a943062824f108fb3f5c135c580a05d6d**。
- 库存/严格服务墙钟测试 **bebac55043dc04be4aefbc464ce28df66c30c30a**；测试准备修复 **d836bad6cf5b8d2ed04aba3811c5296f33fb0f3b**。
- 最终说明和handoff分别提交；所有旧Runner/A21及失败/清理记录保留，不reset/rebase/stash/rewrite。

只新增 src/uaw/run/execution_clock.py；tests/unit/run_clock/test_measurement.py；
tests/integration/run_clock/{conftest,helpers,clock_child,test_transactions,test_persistence,
test_idle_boundary,test_actual_consumers}.py；D requests阶段/最终说明，独立D handoff。
不改clock_ports/shared/Run背景/预算/原Runner/composition/API/锁/A/B/C业务。
14保护文件的归一化SHA相对A6未变，包含clock_ports、真实Idle、A6 resumer/segments/entry、
预算、共享port/类型/schema/锁/旧Runner native源与A21最终说明；git diff --check通过。

## 固定构造与同事务消费

```python
from uaw.run.clock_ports import ClockChange
from uaw.run.clock_sources import RunIdleEffects
from uaw.run.execution_clock import ExecutionClocks
from uaw.run.execution_segments import ExecutionSegments

clocks = ExecutionClocks(records, effects=RunIdleEffects())
clock = await clocks.current(actor, run_id)  # 当前已提交原快照，读取不是执行许可
# A已持有conversation:<原id>锁和原RecordTransaction：
clock = await clocks.change(tx, actor, run_id, ClockChange(
    clock.revision, "waiting_for_user", waiting_item_ref=original_question_item_ref))
# 以后A在同一tx写input_revision/completion_mode前必须重读binding；不能覆盖D clock_ref。
```

精确 `ExecutionClocks(records, *, effects:ClockIdlePort, now:Callable[[],str]=timestamp)`。
必需库存未装配503；构造不启动线程/进程/网络。关闭没有新方法：无自有后台资源，原records/Database
生命周期归A。默认兼容是A未注入conversation_clocks时保留旧路径；不创建假clock或私有新port。

A6候选装配示例：`container.conversation_clocks=clocks`、
`container.conversation_segments=ExecutionSegments(records)`，由A在独立新实例start前安装，
不热改H01-v5。clock不签发权限、lease或deadline；只改clock与binding的clock_ref/revision。
current使用同拥有conversation读事务核对原owner/Run/protocol/input/clock/current pin和rev1 immutable limit，
返回已持久化快照；纯remaining_active_ms(可信时间)或measure只读，不领取时间/持久化投影或改原ref。

change加入同一个A RecordTransaction，严格schema/归属/CAS。pause核对实际open问题/稳定Item/原decision
及hash/input版本，必需真实effects.check；await后再核对clock/binding/owner/问题/账本/新时钟。
非法/nonNone/异常/取消不fallback，不把提案空引用当idle。active/waiting分计整数毫秒、真实超额保存；
倒退412；active耗尽409不可再领，stop仍可保存真超额；取消/终态只可stop，stopped不可复活，
stop即使提案为空也保留原未决引用。新状态/日期不进入请求体。
终态waiting可如实stop而不假称问题已answered；恢复仍拒绝任何open问题。

## 实际验证与完整失败

最终固定A6批次 **54 passed / 99.90秒，1未选的严格跨墙钟节点另跑失败**：
**8纯计量＋46真实D55435 SQL**，没有最终组件skip/error/failure，不把外部接线失败算通过。
accepted-nodes.json来自该批54个不同节点，不累加阶段重复；A节点和旧695/Runner回归不混计。

- 纯计量：天/毫秒、UTC等价时间、主动/等待/停止分计、真实超额/剩余0、倒退拒绝、原limit不变。
- SQL：两次1200秒/1800秒可信模拟等待，重建实例；原段/上限不重领，长等待原deadline保持。
- 并发：同expected revision只有1赢家，另一409；同键重放原结果不再计时。真实2个隐藏新进程
  并发CAS及第3进程重启读取完全相同原段，均finally关闭；标准库Popen在工作线程等待，不阻塞事件循环。
- 原外事务失败clock及binding全部回滚；取消/终态/超额/owner/input/Item/question版本/pin变化拒绝，
  coherent新clock+新pin也不能抬高rev1原上限。原Run/预算/input/admission字段未被D修改。
- 必需Idle缺失、nonNone、异常、取消、迟到clock/问题/取消来源变化拒绝并全回滚；无回退或空数组自证。
- A实际RunIdleEffects：原模型已finished且billing_pending允许真正idle；model claimed/unknown、live held、
  原accounting的未结算reservation拒绝。Tool unknown/confirmed使用明确的持久元数据fixture验证同一真实
  Idle adapter，没有执行Tool或签发假效果。实际取消停止等待clock，保留pending费用和原问题取消记录。

真实SQL/原队列/Run/补充/库存/Model adapter装配可用；模型HTTP回复、provider可用性、服务时间和回答是
明确受控fixture，没有真实模型新调用或新账单，不把pending抹成零费用/无外部效果。
无native窗口、用户文件、旧首次签名文件链、OS Runner key/pipe操作。旧本机链仍独立未完成。

运行源码及接口构造兼容检查Mypy通过（1新源码＋ignored typed构造例）；Ruff/9文件格式通过。
回执ignored tests/.artifacts/D/MS-K1。初轮所有red/失败均保留：缺实现、fixture未走admit、
非法RefKind/决策namespace、fixture model_policy字段错误、D开放问题读图异常/终态stop、
Windows selector不支持asyncio subprocess（改用隐藏Popen工作线程）、pytest保留参数名、
新增fixture accounting主键/导入错误、GBK脚本读取及初轮类型/格式、mypy -c配置冲突等。
未删检查或延长生产期限。最后格式后的测试参数修正已复跑通过。

## M4：实际A6消费及仍缺输入

A原完整队列/补充/新段/终态首批5项62.76秒通过，但late-answer只对部分A服务注入未来时间，
**不作为严格跨墙钟成功证据**。D已加严同一测试：conversation_resume也使用同一个未来服务时间，
保留原成功断言，实际 **1 failed /12.42秒**，A6返回503/conversation.new_active_execution_segment。
A已告知修复自身条件位置：只有segments is None才检查旧墙钟，open问题始终阻断。
最后核对远端仍无正式ms-i2m-a7标签/SHA，D没有消费未发布源码或合浮动integration。

A下一步：发布准确A7 source/正式DISPATCH后，在独立候选实例消费最新D运行源码，
先复验该严格跨墙钟原测试；原Invocation/ctx/账本/审批/root/native期限不续期，旧lease不复活，
A实际新段/更高fence和当前权限/费用/模型/取消仍各自复核。D不修改A resumer来私自绕过503。
新的真实固定模型、实际时间长等待、B页面、独立质量评测与本人H02/成果接受均pending。
Tool跨旧墙钟claim缺A6明确time port时仍保守拒绝；本包不触及C原Tool或旧Runner。
缺输入具体：正式A7修复源/实际候选服务安装及真实模型/本人测试回执；不是缺D clock构造或Idle库存接口。

## 清理与退出

最终批及新增阶段跟踪50个随机fixture主体，含各自platform，共100个精确owner ID：
uaw_records/record_versions/requests/outbox/consumer_receipts均0行；只查本轮精确随机ID，无truncate/他库操作。
之前未跟踪批次依赖原fixture finally清理且无teardown失败，未冒称有独立统计。
A模型fixture的临时Windows provider凭据沿其原finally delete，测试没有teardown错误；D没有provision
真实Runner keys/pipe。3个D自有隐藏SQL子进程均退出，CIM未见本轮自有pytest/child残留。
不打印密钥/数据库URL，不访问用户既有凭据或项目。原Runner/A21失败和清理字节不变。

源码/最终文档和独立handoff各自提交，最终工作区干净；本包交付边界停止，不自动扩包。
严格跨墙钟和生产依赖明确pending，不宣称P1-14/H02/MS-R2/全仓accepted；
flags/checked_metadata/子Agent/DAG/写入安装exec关闭，固定用户模型/原文/权限/取消/CAS保留。

```powershell
. ./ops/start-dev-db.ps1 -Session D
.venv/Scripts/python -m pytest tests/unit/run_clock tests/integration/run_clock -k 'not late_answer' --require-postgres -q --junitxml=tests/.artifacts/D/MS-K1/final-all-a6.xml
# A6严格跨墙钟原失败：以后仅在正式新源接线后复验，unknown不自动重发。
.venv/Scripts/python -m pytest tests/integration/run_clock/test_actual_consumers.py -k late_answer --require-postgres -q
.venv/Scripts/python -m mypy src/uaw/run/execution_clock.py tests/.artifacts/D/MS-K1/protocol-check.py
.venv/Scripts/python -m ruff check src/uaw/run/execution_clock.py tests/unit/run_clock tests/integration/run_clock
.venv/Scripts/python -m ruff format --check src/uaw/run/execution_clock.py tests/unit/run_clock tests/integration/run_clock
```
