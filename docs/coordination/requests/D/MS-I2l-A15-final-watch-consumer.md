# D A15 最终交付：SQL-only 变化监控 + 独立本机失效

实际worktree `E:/UAW/.worktrees/runner`、分支 `dev/runner`。
准确来源 `ms-i2l-a15-source / 1af0a8967ada3b92870c15151f73b31ab09b27e0`，远端peeled tag与HEAD核对一致，
正式派发metadata `635030c02358d54e3d37f593822d189522e2cc93` 已读；只合固定tag，uv sync --frozen成功。
本轮沿原MS-I2l-A9预算修复，保留A13及更早提交/handoff/失败，不进入新共同包。

| 交付点 | 精确 SHA |
| --- | --- |
| M1源码/本机监控/端点消费 | c5b310f223337abd2c11b90670ae277763d36ffa |
| M1构造/覆盖阶段文档 | 492d825ebcf9d31b430788994134fdc34d5f875c |
| 原预算失败与A最小输入 | 6247b720a5d10d498d555fcbf6e7b7aa72a2cabc |
| M2真实source/Windows/原journal验证源码 | c3153522617a719e9f92f922116f54418d946544 |

最终说明与handoff独立提交，实际SHA见Git回执；没有改A Run/SQL/installed/公共schema/ports/锁或其它worker。
13份公共/A/锁规范化hash与准确基线一致。改动文件见Git上述两个源码提交，均D local_runner、D tests/requests。

## 构造、检查点与语义

实际例子和SQL owning paths覆盖表见 [M1阶段](MS-I2l-A15-stage-watch-consumer.md)。
A15已将同一RegisteredRunnerRechecks传入D helper，D runtime为同一NativeRootSource注入LocalReadInvalidation。
原Runner/Factory/Helper构造兼容；公开RunnerReadCurrentPort不改。
内部新增 `IpcSigner.check_private()`、`AuthenticatedPipeSession.check_local(*, deadline)`；
`ReadOnlyPipeEndpoint(..., local_monitor=None)` 默认无完整组合时继续原full session.check。
SQL wait_changed在自己的task初次完整current/捕获，之后fresh UNION；结果永远不授权。
独立本机connection loop马上开始；同一个原Reader、纯factory和实际SQLite journal决定active/原恢复分支。
active组合SQL+真实native Ticket/grant/signature/OS根scope；任一路普通返回、错误、过期、取消都停止work并drain。
原完整current、签名/私钥、Root/actual handle、lease/fence/flags/取消、准入与执行CAS、签名journal效果边界全保留。
恢复（含重复command的已签名prior）不启动active SQL execution current，不重派unknown或使用关闭channel。

双方role/current key/digest/revoke、原PID+创建时间+SID+logon SID和live pipe逐轮真实复查；本机OS private当前解析
与公钥匹配。对端私钥由原真实nonce握手/frame/command/登记双方proof验证，不伪称新remote挑战或读取远端vault。
immutable身份/root比较字节只用于失效对照，不是allowed缓存。这里没有新增IPC wire、pair.complete或生产许可。

15/90秒启动、10秒reply、30秒lease、120秒root和更早源期限不变，所有等待使用本来绝对deadline；
间隔仍50ms，不能用SQL unchanged、自报owner/path/approved或SID/PID独自生成UAW账号权限。
原receipt域/Usage/content Ref version1保持；Runner ok不推Tool业务成功，失败不推not_applied或零费用。

## 本轮真实验证与受控边界

去重 **271不同节点通过**，不是一次全量：

| 验证 | 实际回执 | 范围与受控项 |
| --- | --- | --- |
| 248 D受影响回归，176.38s | regression.xml/log | 原admission/read/crypto/SQLite/OS句柄/取消/idle/37composite/9deadline；新普通return终止、10实际本机失效、实际监控双进程一次读取/重复原journal恢复 |
| 8 D SQL消费者 | sql-final.xml的7通过 + deadline-final.xml的1通过/3.20s | 原真实Run/lease/device/policy/budget/model固定binding/config变更；local monitor/native/channel/gate为组件fixture |
| 15实际installed source变化，910.58s | sql-sources.xml/log | 原Web/SQL/双方OS keys/双进程来源，账号/登记/候选/native账号SQLjournal/stop/provider/model/approval/budget/policy/lease/device/Run/config/role；Runner执行等待与native/初始flags/provider/审批明示fixture |

实际installed 15项为command1/open0：删除或改变**本用例拥有且实际捕获**的原输入后，SQL/current或真实管道/身份失效
停止受控execute等待；不声称Runner真实执行成功。为了选mutation目标，fixture限定自身两个账户下raw SQL lookup且
比对owning捕获地址hash；不是新增生产range来源或宣称arbitrary SQL被观察。没有输出值/秘密或allowed缓存。
旧5个installed验证在新地址测量wrapper中又复验，最终按同一节点去重，不与第一次5项相加。
原sql-final批次13项/343.57s含1个deadline测试期望错误，其他12项通过；只复验deadline修正节点，不重跑整个批次。

实际D monitored IPC组件读取后原文件unlink/authority fixture取消，重复command读取原signed content Ref/body/Usage，
current/wait_changed调用都为0，未新开文件；另一原hidden helper测试回复丢失/文件变化/进程重启，实际open总计1，
原签名快照完全相同。两者来源明确受控组件，不是假冒A首次成功或真人配对。
真实签名、篡改、并发/重启admission、Root版本/撤销/期限/主体及原journal回归均仍在248节点范围。

静态：Ruff通过，37文件格式通过，Mypy36 D源码通过，git diff --check通过。
原stage import collection error、初始Ruff/type错误、model fixture没有model.policies读取的失败与deadline断言错误均保留，
修复后的节点覆盖最终并集；没有xfail/skip或删成功断言，没有重跑旧695/汇合全量。

## 原首次链仍失败：新临时Run独立复验

两次均保留原成功断言失败，分别为84.42s和59.28s；每次独立新Run/临时根/命令，不重发上一unknown。
首次并行验证command1/open0，claim0/signed0/published0；之后排除同轮D测试争用的新Run：
**command1/open1、execution claim1、receipt_data/ref均空**，原deadline在**打开后的fresh current**等待中终止。
未到实际内容read或receipt签名，不能把一次打开叫一次完整读取，不能恢复不存在的回执或推零费用/not_applied。

| 最新独立实测 | 值 | 口径 |
| --- | --- | --- |
| Web→ready / assembly | 18.256s /0.374s | 墙钟阶段 |
| 原approval query / controlled decision | 2.169s /0.554s | 墙钟阶段 |
| approved facade→失败 | 34.856s | 含来源/原注册/发送，不是延长reply |
| endpoint / execute | 9.166s /8.419s | execute嵌套 |
| 3 runner.current | 8.088s累计 | 原效果检查，不是独立墙钟 |
| 6 composite.current | 11.246s累计 | SQL monitor initial与execute并行/嵌套，不与墙钟相加 |
| SQL witness/poll | 92次 /0.869s累计 | 初次完整source仍有成本 |
| local connection current | 134次 /2.300s累计 | 不重展开SQL图 |
| parent /child 全阶段get | 8209/7118次，21.048/14.274s累计 | 含ready/native/审批/注册及reply，不能直接当单个reply查询成本 |

所有6次composite与1次wait_changed deadline完全一致；production checked_metadata=False，原期限未加。
原budget输入文档记录第一次；ignored isolated-chain-summary.json/first-chain-summary.json保留两次精确源成本。
A此前另一个新临时实例command1/open1也没有signature，是独立证据，不覆盖D这里的失败或汇合验收。

## 清理、A接线与停止点

本轮26个installed实例全部验证4随机凭据不存在、2角色key撤销、child退出、proof pipe关闭；
30份D Windows IPC随机namespace原回执全部cleaned=true。无自有本轮helper/pytest残留；D55435仅自身库ready。
未操作其它worker/库、既有用户凭据/进程或用户文件，未新弹本人窗口/自动批准/调用模型。
精确回执与查询成本位于ignored `tests/.artifacts/D/MS-I2l-A15`：accepted-nodes.json、validation-summary.json、
installed-cleanup.json、ipc-cleanup.json、所有原XML/log/metadata/phase文件，不打印私钥或正文。

A接线不需要新增公共DTO/port；消费同一原registered current/Reader/owner/keys/registry/root对象，继续优化
自己所属原注册/发送/重复source costs，保持早期限与完整语义。具体最小参数见
[原预算输入](MS-I2l-A15-control-budget-inputs.md)，D的check_local可用于已审计control/device本机观察，不能独自认证账号。
新生产来源若绕过绑定Database/get/transaction或外部原生源，必须新证明，否则保留full monitor/不可用。
A首次读取→签名journal→原Tool恢复/固定模型材料/引用/Verification/本人浏览器接受与整轮全量仍pending。
D本组件交付到此停止，不自动下一包、不接写入/安装/exec，不代选D01/D03/D06或开flags。

```powershell
. ./ops/start-dev-db.ps1 -Session D
.venv/Scripts/python -m alembic upgrade head
$env:MYPYPATH='src;apps/local_runner'
.venv/Scripts/python -m mypy apps/local_runner/uaw_runner src/uaw/workspace
.venv/Scripts/python -m pytest tests/integration/runner/test_sql_read_watch.py tests/integration/runner/test_installed_watch_boundaries.py --require-postgres -q
.venv/Scripts/python -m pytest tests/integration/runner/test_installed_file_chain.py --require-postgres -q
```

受影响248回归的完整路径列表保留在本轮命令回执；不是上面几行命令合成一次全量通过。
