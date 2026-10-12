# D 原预算修复续项：消费 A15 SQL 变化监控

本文件延续用户已授权直接发送给原 Session D 的 MS-I2l-A9-D-original-read-budget 修复。
不是新共同包，不修改旧标签、D 分支历史、原失败/handoff 或 B/C 交付点。
只有远端 DISPATCH 正式公布 ms-i2l-a15-source 和完整准确 SHA 后开工。
用 git show origin/integration:docs/coordination/DISPATCH.md 核对正式记录，
source 标签中的准备状态不构成再次停工原因；不合并浮动 integration。

## 固定输入及允许目录

A15 已合入 D 最终 13ecd4bd / 9f8d0f1 / cde9eca，保留所有原提交。
InstalledReadOnlyHelper 通过 super 显式传同一个 current_source；peer/root/bootstrap/服务/records 绑定检查已增加。
RunnerReadCurrentPort 的 current/wait_changed 签名不变，生产 checked_metadata=False 保持。
A15 补齐 A14 漏掉的事务 load，实际 lease/device 撤销通过；真实双方 peer SQL coverage 已验证。
具体覆盖、限制及 163 定向回执见 MS-I2l-A15-transactional-watch.md，不把全部来源等同 SQL。

D 自行核对准确标签并在 E:/UAW/.worktrees/runner、dev/runner 合入固定来源。
仅原 D 允许 apps/local_runner/uaw_runner/、D tests、D requests/handoff；不改 A SQL/Run/installed、
公共 schema/ports/锁或 B/C 业务。不替 A 打开 flags、缩短校验或扩大原期限。

## M1：监控方案、显式消费与阶段交付

1. 审计实际 command current 捕获的 SQL 输入，确认原 Web 账号、双角色 enrollment、
   launcher candidates、native **账号确认 SQL journal**，以及原 Run/配置/provider/审批/预算/lease/device
   均经已绑定 Database/records/transaction load。只说本 production 图，不声称 arbitrary SQL/range 覆盖。
2. 将 SQL 变化监控与独立本机失效监控组合，避免后台每 50ms 完整重展开双方账号与政策图。
   wait_changed 本次初始完整校验后仅 fresh UNION；任何返回/错误/期限终止都取消原 work，不能产生许可。
   不能把旧允许值跨 task 传给监控，也不能缓存 allowed、加大 sleep、删检查来换预算。
3. 独立保留真实双方 role/key/public digest/撤销/公私钥、PID+创建时间+SID+logon SID、live pipe、
   本机 native SQLite Ticket/grant/签名/expiry/root 当前状态的监控及效果复查。
   原 immutable peer/proof/身份只用于对照，不是权限。缺少明确廉价本机接口时先提交具体提案给 A，
   保留原完整监控，不能只接 SQL watch 就宣称监控闭合。
4. 原 first-byte owning reply deadline 固定传递；所有更早 command/lease/root/session/key 到期不增加。
   普通 15 秒/首次 90 秒启动、10 秒回复、30 秒 lease、120 秒 root 均保持。
   原 recovery/journal 继续独立数据权限，不能调用 active execution current 来拒绝原可访问旧回执。
5. 阶段交付准确 SHA、检查点/覆盖表、实际构造与 A 必需参数，随后继续 M2。
   A 到阶段即审阅接线，不等待最终全包；若需新 A 适配参数，由 A 修改自身源码。

## M2：实际预算与原回执链

1. 保留签名命令、native owning scope、准入/执行一次使用 CAS、lease/fence、OS 根/文件句柄、
   打开/读后/签名/发布后的 fresh current 与原效果 guard；不从 SQL watch 返回值推断可以执行。
2. 回归等待中账号退出、登记/候选/native账号确认SQL journal变化、lease/device/Run/模型/provider/
   审批/预算/政策变更，以及双方 key/OS/live pipe/native root 变化。实际变化须终止原 work。
3. 运行真实 Windows 原临时材料首次文件链：一次发送、一次实际打开、原签名 journal、
   回复丢失后的原 journal 恢复。unknown 不重发；不操作真人窗口或用户目录。
4. 精确记录源耗时、调用/SQL次数、原 reply deadline、command/open、失败和随机凭据/keys/child/proof 清理。
   同图嵌套累计耗时不与墙钟相加；组件耗时与完整首次链分别报告。
5. 如首次读取仍失败，交付组件及具体停止点，不放宽成功断言/xfail/skip/期限，不自动扩包。
   最终源码与独立 handoff 提交；完整 MS-R2、模型文件交付、本人接受和汇合全量不由 D 标通过。

## A 同时推进

A 负责原注册/发送、生产账号/角色/model/provider/Run 与工具/审批所属服务来源成本及装配。
D 阶段 SHA 到即合入，A 只改自己的参数/适配器，不接管 worker 业务。
真实首次链通过后接原材料低信任 Context、固定用户模型、准确引用/Artifact/Verification、原页面本人接受，
汇合后才做全量；B/C 当前没有新增任务，不制造缺来源的等待包。
