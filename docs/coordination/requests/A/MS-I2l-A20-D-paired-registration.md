# D 续项：同次 IPC 双角色联合登记消费

这是原 MS-I2l-A9 文件预算修复续项，不建立新共同包，不重做已接受A15监控。
**开工来源：远端 DISPATCH 正式记录的 ms-i2l-a20-source 与准确 SHA**。
A先发布source和派发记录；D自行fetch核对tag peeled SHA及正式记录，再合这个固定source。
不能按本文件准备状态或浮动 integration 开工。保留 D c315352/9225919 与所有原回执；
不 reset/rebase/stash/重写提交；A不操作D分支、环境或工作区。

## 输入/来源/范围

- `EnrolledPeerRegistry.current_pair(control, device)` 已由A实现，准确契约与算法见
  [A20 source](MS-I2l-A20-paired-registration.md)。返回 tuple(control_peer, device_peer)。
- 输入是原实际OS连接双方身份；返回不能来自body、旧peer、SID/PID推断或模型。
- 来源保留原Web拥有者、candidate实际双方OS/key、owning native journal、双签名与原enrollment。
- A20实际Windows测量OS8/key8不减、SQL22→14，完整结果相同；D尚未消费，不是原首次链成功。
- 原A19首次链103.49秒失败command1/open0；A18旧实例open1同样无signedjournal，全部保留。

## M1：消费和严格返回验证，提交即报阶段SHA

在D的 `apps/local_runner/uaw_runner/ipc/sessions.py` 接入可选 paired registration。
接口发现、类型协议及纯返回校验由D设计，但不得改变原必需PeerRegistrationPort.current兼容语义。
有paired方法时一次call固定control/device身份，返回必须严格tuple2、各为RegisteredPeer、
role/order/identity/owner/actor/device/key_ref/pairing_ref/expires匹配原独立握手和current校验。
保留D每个返回对应的独立directory当前role/key/digest/撤销复查、pipe和期限检查。
旧不支持paired的registry继续原两个current；paired存在但返回错误、异常、超时、取消时关闭/拒绝，
**不能fallback再找许可**。混入字典/列表/单值/重复role、swap、错owner/device/pair/key、非有限/过期期限都拒绝。
原handshake/receive/send/check/check_local/原journal数据权限语义不能减弱。
无需公共shared/workspace ports/schema/锁或HTTP变更；提出必须公共变更时先报A，不私改。

M1覆盖新的paired消费者与旧current兼容，发布阶段源码/具体消费接口后继续本续项，不等A最终合入。
A阶段到即接；D不借A实际测量将自己consumer标通过。

## M2：真实边界和原首次链

完成受影响IPC/session单元与实际Windows临时双进程验证，包括：两角色当前key撤销、原owner变更、
OS创建实例错配/退出、真实pipe断连、关键await后撤销、原早expiry/取消、错误paired返回无fallback。
实际A source消费和同namespace/query/owning-check次数测量，保留前后角色/key/权限复查证据；
不将并行/嵌套秒数相加，不引用不同负载的旧墙钟做通用速度比例。

使用D自己的库55435与临时根，单独运行原
`tests/integration/runner/test_installed_file_chain.py --require-postgres` 原完整成功断言：
Tool→审批/预算→实际一次读取→签名journal→原快照恢复。原frame/absolute reply deadline不变，
unknown不重发、不删断言/skip/xfail、不放宽10秒reply/30秒lease/120秒root/启动或更早期限。
若失败，记录新Run command/open/claim/signed/ref、每个停止点和全源成本；无signed journal不得造恢复。
根据具体风险做定向验证，不重跑旧695全量，不为凑计数重复重跑固定失败。

受控native/初始配置/模型metadata、实际SQL/OS/keys/IPC分开标记，不触发真人窗口或访问用户文件。
保留所有失败/中断/费用、不推not_applied/零费用；清理核对随机凭据、keys、child/proof/pipe。
最后独立handoff到原D文档，报告精确源码/目录/依赖/回执和未通过项，本续项后停止不自动扩包。

## 允许目录与分工

D仅改原 `E:/UAW/.worktrees/runner / dev/runner` 的：

- `apps/local_runner/uaw_runner/` 原IPC/session及必要消费装配。
- `tests/unit/runner/`、`tests/integration/runner/` 受影响定向检查/透明测量。
- `docs/coordination/requests/D/`、`docs/coordination/handoffs/D.md`。
- 本D忽略回执/临时目录/环境；数据库只自己的D实例。

不改A `src/uaw/infrastructure/`、`src/uaw/run/`、共享schema/ports/contracts/锁/flags或其他worker。
A继续自己的source/root/Tool重复展开定位和生产装配；A源码错误报具体等待点/最小修复给A。
B/C仍交付停止点。默认固定用户模型，不启用子Agent/DAG/写入安装exec，不代本人确认或接受。
