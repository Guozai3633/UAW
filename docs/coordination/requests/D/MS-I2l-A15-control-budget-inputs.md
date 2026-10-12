# D A15：原回复预算剩余输入与 A 接线要求

来源固定 `ms-i2l-a15-source / 1af0a8967ada3b92870c15151f73b31ab09b27e0`。
D M1 `c5b310f223337abd2c11b90670ae277763d36ffa` + 阶段文档 `492d825ebcf9d31b430788994134fdc34d5f875c`。
不改A源码/公共契约，不新增deadline、不移标签、不把原unknown命令再发一遍。

## 实际首次链结果与成本

D原55435独立临时实例在本源码原测试断言失败，84.42秒；不是组件测试失败被改成skip。
command1/open0，file_read_attempts0、signed0、published0，4随机凭据清除、2keys撤销、child退出/proof关闭。
初始OS/SQL来源真实，native选择/首次provider/flags/审批为既有受控fixture，不是真人接受或生产权限。
同一个first-byte reply deadline传给3次current和1次wait_changed，没有延期。

| 实测位置 | 本轮值 | 口径 |
| --- | --- | --- |
| 原Web→callback ready | 23.626s | 墙钟阶段 |
| 原审批query/受控decision | 2.626/1.180s | 墙钟阶段 |
| approved facade→结果失败 | 50.812s | 含原注册/来源/发送，不是新的回复上限 |
| parent command register/collect | 6.285/2.949s | collect嵌套于register，不能相加 |
| parent pipe | 10.012s | 原10秒 owning exchange |
| D endpoint dispatch | 8.695s | 原更早对端期限已消耗前置检查，不扩大 |
| D runner.execute / current | 7.417/6.764s | 嵌套累计，不与墙钟相加 |
| composite3次 | 11.241s累计 | 含SQL watch initial与执行task并行，不能说墙钟11秒 |
| fresh watch SQL witness/poll | 46次 /0.951s累计 | 初次owning完整语义有额外成本，不是零成本通知 |
| local connection checks | 94次 /3.661s累计 | 实际OS/双方key/本机private，非SQL允许缓存 |
| 全阶段parent/child get | 8252/5471次 | 30.396/14.896s累计，含ready/native/审批/执行；不是单个reply SQL成本 |

实际命令捕获含web.sessions、双角色enrollments、launcher.candidates、native.decisions、原command/Tool/
Run/config/model/provider/role/policy/approval/budget/attempt/lease/device，历史configs/inputs/models也在owning图。
停止在准入current尚未完成第二轮，未claim/open/生成receipt；保留原diag CancelledError及实际失败。
本轮D来源CPU/SQL共用本机，不据跨轮51/74/84秒直接宣称性能提升或退化百分比。

## A 必需接线与可继续优化位置

1. A15 InstalledReadOnlyHelper已有same current_source绑定，D无需新公共参数：runtime同步装配SQL-only变化
   与真实本机invalidations。实际效果current/Reader/owner/签名/Root/lease/fence/flags/CAS不减少。
2. A原RunnerPipeClient.read的owning10秒从独立actor/Reader/session检查开始；send/receive仍各自fresh校验。
   不应为了child成功把这个期限改晚。建议A按原固定Ref/actor/channel与same records，记录各前置来源
   查询成本，优化自己所属的重复语义展开/登记发送；D不能在A接口里偷接元数据或打开checked_metadata。
3. 若A后续需要control侧廉价本机复查，D已提供内部真实
   `await actual_session.check_local(deadline=original_absolute_deadline)`，control/device均支持local signer当前
   role/public/revocation与实际OS credential持有。它只观察本机失效，不替代完整registered account/proof current。
   其配套SQL watch与native root sources的拥有关系、当前command捕获闭合和原期限仍必须由A自己审计装配。
4. 缺少A消费端原命令/current/独立注册身份/Root来源绑定时继续不可用或保留完整监控；不从SID/PID/body
   approved自建owner，不新增pair.complete，不缓存allowed，不以一条SQL unchanged准入。
5. 原journal恢复入口仍是原数据权限，不能拿active SQL execution current拒绝已允许旧回执；未签名unknown
   必须保持不可用，不能补造receipt、不重dispatch/open。D组件真实journal恢复与A首次结果分别验收。

精确元数据见ignored `tests/.artifacts/D/MS-I2l-A15/first-chain-summary.json`、chain.xml/log和原临时回执。
M2继续派发范围内变化/重启回归；完整MS-R2、固定用户模型材料交付与原本人浏览器接受仍pending。
