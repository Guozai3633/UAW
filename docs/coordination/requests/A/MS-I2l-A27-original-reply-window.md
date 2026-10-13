# A27：控制端原回复窗口与子进程关闭传播

2026-10-13，继续 A26 发布 HEAD，只有 A 源码及 A 测试发生变化。
不修改 worker 业务/分支，不扩大原计时窗口。

## 真实时间关系

之前 child 的 ipc_closed 并不等于它自己的回复 deadline 已到。此次把 parent 与 child
观察置于同一个本机单调时钟，记录起点、绝对 deadline 相对共同零点的位置、剩余时间、
完整来源校验/发送/接收/关闭及关键操作返回状态；不记录账号、目录、参数、正文或凭据。
所有 trace 仅在本次交换结束后落盘，不加入效果检查点的 I/O。

初次原成功断言仍失败（54.06 秒）：parent 原 10 秒窗口从共同时刻约41.364开始，
截止约51.364；source/会话复查后约41.736才开始send，41.878开始receive。
child 原frame窗口截止约51.809，晚于parent约0.445秒。parent约51.390响应取消并关闭，
child仍在读取后的第四检查点；打开和读取已返回，未完成receipt签名。
约0.027秒的超出包含取消/OS排空，不意味着允许新的效果或延长原截止。

这是本次调用的真实观察，不是机器/数据库稳定速度或全部旧失败的唯一原因。
计算量仍超出整体回复预算，deadline关系本身不是延长窗口的理由。

## 实现与修复边界

`RunnerPipeClient.read` 将原同一范围内的相对timeout明确为一次计算的绝对deadline。
开始点仍在原source检查前，actor→command→session→send/receive或原journal→验签→
重新source与session复查全部在同一 `asyncio.timeout_at` 中。

新增内部 `_exchange(ref, channel, *, recover, deadline)` 是该单次窗口的观察边界，
没有新HTTP、DTO、wire字段、开关或body deadline；会话仍执行D原bounded内部操作。
不会在发送后重置parent窗口或自动恢复/重发未知命令。

新增 `_reply_current(deadline)` 在实际await之后和返回前显式检查：

- 当前Task若仍有取消请求，重新抛CancelledError，依赖不能吞掉调用者取消后继续发命令。
- 原monotonic deadline已到，拒绝迟到结果；asyncio.timeout取消若被依赖吞掉，也不能变为成功。
- source、command、session检查后的发送前、send后、receive/journal后、验签后及最终复查后检查原窗口。
- 出错继续原close与busy清理；不把unknown推成not_applied、零费用或新执行许可。

显式期限检查修复的是“依赖吞取消仍继续”的独立正确性缺口，不能当首次链性能问题已解决。
保持原来源校验、签名/hash/attempt/device绑定、恢复独立数据权限以及最后source完整比较。
不删D effect checkpoints/OS/key/handle guards，也不改变10/15/90/30/120秒及其他较早期限。

## 验证

初次8节点控制端回归通过；新增故障依赖后11节点通过，补验uncancel后最终12节点通过，含：

- source等待消耗原窗口且从未send/open。
- receive等待不得重新获得整段时间，已send命令仅一次，二次execute拒绝。
- pending时并发调用拒绝，取消后close/busy清理。
- source或receive故意吞掉timeout取消，不能越过原截止继续发送/返回成功。
- source故意吞掉timeout并清掉Task取消状态，仍由原deadline显式拒绝且正确分类为timeout。
- source故意吞掉caller取消，仍按取消停止、send0/open0。
- 原SQL/crypto夹具的字节、签名、受控丢回复后原journal、篡改拒绝与独立data权限继续通过。

这些控制端用例是真实SQL/crypto＋受控pipe，不能当实际native人授权或真实执行链通过。
真实首次Windows/Web/SQL/双key/IPC链与临时root/SQL用户决定另外保存，原恢复成功断言不放宽。
初次import/格式准备问题已修；完整类型、静态、接口检查和最终实际停止点以证据为准。

[A27实际回执](../../../implementation/evidence/ms-i2l-a27.json)。BCD原交付保留，无新包、不自动同步。
flags/checked_metadata/子Agent/DAG/写入安装exec不启用，无用户文件、新LLM或本人操作。

## 最终固定结果

12 个不同定向节点通过，215 源码类型、4 文件静态与格式通过；610 历史并集未全部重跑。
487 源码摘要固定，旧1691全量和费用不覆盖。修复守住原deadline/cancel，不证明实际首次链完成。

修复后原成功断言单独复跑56.16秒仍失败；parent窗口从约42.649到52.649，
send从约43.098开始，receive从约43.247开始。child截止约53.200，晚于parent约0.551秒。
parent约52.659关闭；child停在打开后的第三检查点，没有完成正文read或receipt签名。
两次的执行进度不同，不把总秒数或最后到达的检查点当稳定性能提升。

每次原command只发送一次、一次使用占位1，持久signed_data/ref0，原字节和journal恢复断言未到达。
unknown未重发、不造journal或零费用。两个临时installed实例随机凭据移除、双方key撤销、
child退出和proof关闭全核对。所有实际整链失败和初次8节点回归保留，未mark整轮accepted。

剩余问题是全量来源复查的实际累计耗时，不是取消传播失效。A继续自己同源来源收敛，
默认不让已发命令重新计时，也不为通过测试延长期限。BCD无新协议或新包，保留原交付点。
