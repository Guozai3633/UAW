# D A15 M1：SQL 变化与独立本机失效监控

实际 worktree `E:/UAW/.worktrees/runner`，分支 `dev/runner`。
准确固定来源 `ms-i2l-a15-source / 1af0a8967ada3b92870c15151f73b31ab09b27e0`；
远端 annotated tag object `0c1b7b51c3f0fa7504042c5bde29e2fb48fd6b73`，peeled commit一致。
已只读核对远端 integration DISPATCH 的正式 A15 派发，快进后 HEAD 精确一致，uv sync --frozen成功。
M1 源码 **c5b310f223337abd2c11b90670ae277763d36ffa**。原A13提交/handoff与失败回执保留。

## 构造与停止语义

公开 RunnerReadCurrentPort 不变，A15 InstalledReadOnlyHelper 传来的同一个 current_source
由 D runtime 自动与 `LocalReadInvalidation(helper.roots)` 组合。直接构造示例：

```python
endpoint = ReadOnlyPipeEndpoint(
    session=actual_session, registry=actual_registry,
    commands=original_registered_reader, runners=original_factory,
    current_source=registered_runner_rechecks,
    local_monitor=LocalReadInvalidation(actual_native_root_source),
)
await endpoint.serve_once(deadline=original_first_byte_reply_deadline)
```

A必需参数仍是同一个 actual source/records/Database、Reader、registry、EnrolledPeerRegistry、
NativeRootSource、directory、OS CredentialStore，local device signer/credential与Runner device binding相同。
不能把其他未审计 SQL/range/ad-hoc 来源借同名port冒充本图覆盖。
无 current_source 或无 local_monitor，保留原每50ms完整 session.check；不默认只接SQL。

`watch()`原无参签名保留，保存本次固定frame/期限仅选择独立原Ref。
actor取 registry中已认证握手的完整主体，Reader独立读owner/command，不接受body内归属。
本机connection检查立即开始，不等待Reader或SQL初始化；独立Reader/纯装配后选择active或journal恢复。
active支路在自己的task调用wait_changed：初始完整current与捕获不借用执行task的任何allowed值；
此后A一条fresh UNION观察已捕获current/history/absence。SQL返回也视为变化，任一路错误/到期/取消
均停止原work、取消并drain监控兄弟；原dispatch效果完整current/guard/CAS全部保留。
已签名prior journal（包括重复command）及显式recover仍走完整数据权限监控，不启动active SQL current。

## 本图来源审计与边界

| 来源 | 本次 owning 捕获路径或独立本机检查 | 保留的效果复查 |
| --- | --- | --- |
| Web完整账号/session | collect →devices.channels.session→session.check→EnrolledPeerRegistry→enrollments.actor→原browser_sessions.principal，RecordStore.get | fresh current/独立Reader |
| 双角色enrollment/launcher candidates/native账号确认SQL journal | 原同Database enrollments records、candidate及native.recorded，含RecordTransaction.load observer | 双方原proof/签名/owner当前语义 |
| 原command/Tool/Run/model/provider/policy/role/config/approval/预算/attempt/lease/device | collect两轮已绑定store/transaction读；历史/缺失也捕获；不含arbitrary SQL/range | 每个执行边界fresh current、准入/执行CAS |
| 双方当前role/key/public digest/撤销 | session.check_local fresh directory；对照原握手角色key固定Ref | actual command/IPC/receipt域签名与当前key |
| OS 双方实例/pipe | retained peer handle alive、PeekNamedPipe、PID+创建时间+SID+logon SID重新取、实际本机OS身份；握手固定bytes只作比较 | receive/send、关键current、实际文件句柄 |
| 本机device私钥 | 每轮原OS credential解析及Ed25519 public匹配，不输出秘密、不签假回执 | 真正receipt签名再次检查 |
| 对端control私钥证明 | 原签名nonce握手、原command/current enrollment两角色proof；不能从PID或公钥推断私钥，不声称新remote challenge或实时远端vault读 | 接收真实签名frame、原command verifier |
| 本机SQLite目录选择 | NativeRootSource._read：已消费Ticket/document hash、grant/签名/current device key/期限、路径与OS根身份，末尾再次读；实际scope/签名 | RootBindings与WindowsReadHandle guard |

这是实际 A15 installed 图的静态审计。实际命令捕获的namespace/SQL成本另由M2透明wrapper记录；
M1不把单独peer测试或受控fixture当作该首次链已闭合。原公私钥证明语义保留，不新增IPC wire挑战。
SQL比较不是跨SQL/OS/SQLite原子grant；所有实际效果检查保留。间隔仍50ms，没有加时。
10秒回复/30秒lease/120秒root和更早command/context/session/key期限保持；恢复不重发unknown。

## 验证与阶段状态

`tests/.artifacts/D/MS-I2l-A15/m1-final.xml`：**60不同节点通过**，47.80秒，无失败/错误/跳过。
4调度double取消/普通返回、10真实Windows双进程本机失效、9原deadline接口、37原composite组件。
本机失效包括control/device撤销、实际随机OS私钥删除、退出/断连/期限/身份错配、根替换/撤销/过期；
所有根为D临时根，原UAW注册/权限/native输入仍明确fixture，不是真人。
`m1-ruff-final.log`通过；`m1-mypy-final.log`36D源文件通过。
初次uv pytest因入口sys.path报tests import collection error，后用原python -m pytest修正；回执保留。
原14节点监控复验18.59秒回执另保留，不重复累计。

```powershell
$env:MYPYPATH='src;apps/local_runner'
.venv/Scripts/python -m mypy apps/local_runner/uaw_runner src/uaw/workspace
.venv/Scripts/python -m pytest tests/unit/runner/test_composite_endpoint.py tests/unit/runner/test_read_watch.py tests/integration/runner/test_local_read_watch.py tests/integration/runner/test_composite_read_current.py -q
```

A到此源码即可以原装配审阅，无新增公共参数/依赖/flags。D继续M2原installed首次链及来源成本、
真实SQL等待变化/原journal回归和清理；不重跑695全量，不把M1组件通过标为首次文件读取/本人接受。
