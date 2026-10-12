# D A20 最终：双角色联合登记 IPC 消费

实际 worktree `E:/UAW/.worktrees/runner`，分支 `dev/runner`。
正式派发固定版本 `ms-i2l-a20 /97681494e173534acc7ac36bf03c48eea233c449`，准确 source
`ms-i2l-a20-source /46dd884f47fad35da19cd310be4e3aba0d45bc58`。干净fetch后只读远端integration DISPATCH，
核对source peeled SHA，快进后HEAD精确相等，uv sync --frozen成功。旧c315352/9225919/handoff/失败均保留。
没有合浮动integration/reset/rebase/stash；只改D允许目录。

| 交付 | 准确提交 SHA |
| --- | --- |
| M1源码/严格返回与无fallback | d32712e4f320b58fb3f313caad19db64f4974c72 |
| M1阶段构造说明 | 76e070889508664a89ce2ff77ac136444fb93340 |
| M2早期限/真实Windows/actual A source测量源码 | 4254a0be4a48ddc1df685ac338ffdbe0bd24bb9e |

最终说明/handoff分别提交，准确SHA见Git回执。10份A/shared/schema/锁摘要与固定source一致。
源码文件为 `apps/local_runner/uaw_runner/ipc/sessions.py`；自己的新unit paired测试、两个Windows/actual source
测试及 installed_file_child透明测量。没有改A source/Run/root/Tool/HTTP/workspace ports/schema/锁或B/C。

## M1/M2接口和效果边界

装配接口见 [M1阶段](MS-I2l-A20-stage-paired-consumer.md)，无需A参数变化。
D内部PairedPeerRegistrationPort只是本机可选typing协议，不是公共DTO/IPC wire。
已有EnrolledPeerRegistry对象在完整session._check自动消费current_pair(actual_control_os,actual_device_os)。
严格tuple2、RegisteredPeer及完整字段/aware期限、固定role顺序/原实际OS identity、owner/actor/device/key/pairing
与原握手匹配；schema复制detaches nested模型，再分别读取独立directory当前role/key/public digest/revocation。
pipe live在源await前后、channel/peer对照和原UTC/monotonic期限等待后仍检查。原private check、nonce/frame/command/
receipt域验证、A15 SQL与本机native invalidation、Runner完整current/Root/handle/取消/lease/fence/flags/CAS保留。
返回值只比较原身份，不缓存allowed。paired存在却非callable/返回坏schema/错误/异常/timeout/cancel关闭拒绝，无fallback。
没有paired方法才走原两次current；初始握手未知双方时仍原single，末尾check及receive/send/journal数据权限自动用pair。

M2补齐等待中的较早session期限：check使用 min(now+原pipe.timeout,原monotonic_expiry,原UTC expiry对应剩余时间)，
只收紧较早期限，不加新预算；endpoint原较早absolute reply仍外层约束。挂起source在这个期限取消并drain。
旧无pair源也遵守同期限。15/90启动、10reply、30lease、120root及原更早command/key等不延长。
恢复仍独立data permission，不由active current拒绝允许原回执；unknown无签名不可用，不重新dispatch/open/造journal。

## 真实消费验证与成本

去重 **106不同节点通过**，非全量：

| 回执 | 实测 | 真实/受控范围 |
| --- | --- | --- |
| ipc.xml/log | 104passed/203.24s | 28新strict unit + 11真实paired await Windows边界 + 原Windows IPC/read/local watch/journal restart/endpoint定向回归 |
| deadline-unit.xml/log | 29passed/1.92s | 同28unit重新验证与新早session expiry取消1项，去重只新增1 |
| pair-actual.xml/log | 1passed/33.54s | 实际A20同账号/SQL/双keys/双进程完整登记经D consumer，native/初始availability明确受控；command0/open0 |

104节点包含真实两角色key撤销、owner完整session错配、OS创建identity错配/退出、管道断连、expiry、关键await取消/
较早timeout、返回swap无fallback、以及原签名篡改/重放/断帧/超长/取消/恢复/临时文件等原受影响行为。
unit uses真实temp SQLite/Ed25519 key directory，但registry/OS/pipe明确double；新Windows registry独立fixture不叫
生产账号/真人配对。actual A20测量才使用原Web会话、候选/native账号SQLjournal、当前双方OS/key和双签名来源。
没有真人窗口/代批准/用户目录或真实模型调用。测试native/root/审批/首次provider/flags始终fixture分列。

同一个真实session、registry和完整peer结果的两种consumer路径：

| 同图单样本 | legacy singles | paired消费 |
| --- | --- | --- |
| owning enrollment检查 | 2 | 1 |
| SQL SELECT | 22 | 14 |
| A role OS实例观察 | 8 | 8 |
| 当前directory key查询（含D独立2次） | 10 | 10 |
| paired/current接口 | pair0，旧两current | pair1 |
| 墙钟 | 0.135245s | 0.096539s |

实际D pipe前后live/OS检查另保留，表中OS是A登记角色观察计数，不把它当所有OS API调用计数。
完整local/peer/channel字节不变；默认checked_metadata=False。同样本减少owning展开，不能报生产整链同比提速。
源测量原文件为ignored pair-actual-temp对应paired-consumer-measurement.json和metadata.json。

初始新sync unit fixture无running loop导致28errors，改async后同节点通过；初次Ruff import/长行记录保留，格式后通过。
最终Ruff通过、5受影响文件格式通过、Mypy36D源通过、git diff --check通过；无skip/xfail或删断言、未重跑旧695全量。

## 原完整首次链失败与具体停止点

按派发**单独**运行原test_installed_file_chain.py成功断言，新临时Run不是重发旧unknown。
**80.78s、1failed**，command1/open0/admission1/execution claim0/signed0/ref0。原成功断言保留，未造恢复。
准入后再取fresh current，停在root/mapping owning来源await，尚未执行claim/OS打开/内容read/receipt签名。
parent pipe原10秒结束关闭连接，本机monitor实际ipc_identity_denied，execute/current被取消。
该诊断证明连接失效，不推断用户撤销或“文件未应用/零费用”。原diag和shielded IPC失败日志保留。

| 全阶段实际成本 | 值 | 口径 |
| --- | --- | --- |
| Web→callback ready / assembly | 25.402/0.454s | 墙钟 |
| 原approval query / controlled decision | 2.462/1.219s | 墙钟 |
| approved facade→failed | 44.839s | 含原来源/注册/发送，不是新增reply预算 |
| register / collect | 5.136/2.390s | collect嵌套register |
| parent pipe | 10.018s | 原10秒owning exchange |
| endpoint / execute | 8.844/7.738s | 嵌套 |
| runner.current 2次 / composite4次 | 7.002/10.515s累计 | monitor initial与execute并行；不与墙钟相加 |
| paired登记/完整session | 118次/118次 | pair累计10.217s，session累计11.908s，含ready/native/dispatch |
| old single / owner / owning总图 | 43/106/267次 | 118 pair +43 singles+106 owner，启动/mapping单独owning检查仍实际执行，非fallback |
| owning图总累计 | 10.072s | 全阶段含nested/parallel，不当一个reply墙钟 |
| root当前来源 | 14次/3.762s累计 | 含重复Run/Tool owning source等待 |
| fresh SQL witness/poll | 68次/1.112s累计 | 不缓存allowed |
| parent/child全阶段get | 7180/5012次，25.400/13.739s累计 | 包含启动/native/审批/登记/执行，不当reply单独SQL计数 |

全部4次composite和1次wait_changed使用同一个原first-byte reply deadline；pair调用错误计数为0，无fallback。
签名总wrapper计数含native授权启动，不能冒认真实execution receipt，持久signed/ref均0。
精确数据ignored chain-summary.json及chain.xml/log、metadata/phase/diag；未引用不同负载旧失败墙钟作百分比。

## 最小 A 输入缺口与接线

1. 同一actual EnrolledPeerRegistry及同directory已经被D完整消费；不需要A新增paired DTO/constructor或打开flags。
2. 现在仍缺**原预算内完成效果前 owning root/Tool/current来源**：此实例admission已完成、post-admission fresh
   current在原root/mapping图等待取消，claim/open/signature均未到。请A继续原root/Tool完整owner/账号/候选/native
   SQLjournal与双签名共同图重复展开定位；需要有界同次joint来源时发布准确内部接口及拥有关系。不能把快peer结果
   或unchanged SQL当权限，也不能删D效果后fresh检查。没有实际A新接口D不能私改其root/Tool图。
3. 原control登记/发送属于A，parent10秒仍包含独立actor/Reader/session/send/receive来源；消费同一个固定Ref/主体/
   原channel/root/lease/fence版本，保留较早期限与取消。A可以审阅本source统计后优化自己的节点，不向D要求假journal。
4. 未签名unknown保持不可用，不重发；待新Run完整实际read/sign/publish通过，才能验证A原签名journal恢复与Tool材料
   交付。D独立真实journal/重启恢复本轮回归已通过，不等于A首次链或固定用户模型材料/本人接受/整轮MS-R2。

## 清理、统计口径与停止

本轮**2独立installed实例**各4随机凭据不存在/2role keys撤销/child退出/proof pipe关闭，67份Windows IPC namespace
原报告均cleaned=true，无自有本轮helper/pytest残留。D库55435仅自己的原库，未操作其它worker/库/用户凭据/进程。
清理按resolved物理路径去重pytest current别名：本轮4个目录名实为2个实例。
同时审计原A15统计“26实例”含4个current链接重复，实际22独立实例，所有原清理断言仍通过；本次只补记口径修正，
不覆写旧A15提交/handoff/失败。修正证据ignored a15-cleanup-count-correction.json。

源码/最终说明/独立handoff提交后工作区干净，本续项到此停止；不自动同步下一源或扩包。
生产checked_metadata/flags关闭，固定用户模型/原文/权限/版本/取消/一次CAS保持；不开放子Agent/DAG/写入安装exec，
D01/D03/D06不代选。Runner ok不自动Tool业务成功，failed/cancelled不推not_applied/零费用。
完整首次读取、原模型文件交付、准确引用/核验/本人浏览器确认与接受/汇合全量仍pending。

```powershell
. ./ops/start-dev-db.ps1 -Session D
.venv/Scripts/python -m alembic upgrade head
$env:MYPYPATH='src;apps/local_runner'
.venv/Scripts/python -m mypy apps/local_runner/uaw_runner src/uaw/workspace
.venv/Scripts/python -m pytest tests/unit/runner/test_paired_registration.py -q
.venv/Scripts/python -m pytest tests/integration/runner/test_installed_paired_consumer.py --require-postgres -q
.venv/Scripts/python -m pytest tests/integration/runner/test_installed_file_chain.py --require-postgres -q
```

104节点完整命令：python -m pytest tests/unit/runner/test_paired_registration.py
 tests/integration/runner/test_windows_paired_registration.py tests/integration/runner/test_windows_ipc.py
 tests/integration/runner/test_windows_read_ipc.py tests/integration/runner/test_local_read_watch.py
 tests/integration/runner/test_monitored_read_ipc.py tests/integration/runner/test_original_journal_recovery.py
 tests/unit/runner/test_composite_endpoint.py -q。回执ignored tests/.artifacts/D/MS-I2l-A20，accepted-nodes.json逐项去重，
validation-summary.json明确通过/保留失败/清理；上方命令不是合成一次全量通过。
