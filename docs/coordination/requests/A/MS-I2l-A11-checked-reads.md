# A11：单次来源检查的重复读取与最终 SQL 复查

继续 MS-I2l-A9，基于已发布 ms-i2l-a10-source / 5f747fd0。
只改 A 的 records、RunnerCommands、EnrolledPeerRegistry、注释与 A 测试；
不修改 B/C/D 业务实现、公共 wire 或 flags。准确后续源码由 DISPATCH 发布。

## 为什么调整

A10 的原 Windows 链仍 command1/open0，第一次 current 6.673秒。
A11 第一轮只接 RunnerCommands：73组件通过，实际链72.13秒失败；
command1/open0，未知结果不重发，原凭据/keys/child/proof pipe清理。
失败链两次 current 合计4.682秒，通道 session_current 检查仍累计较高。
这些是嵌套/并发阶段累计数，不能直接相加作为一次调用的净时长。

## 范围与实现

`PostgresRecordStore.checked_read_batch()` 是内部 async context manager：

默认 `PostgresRecordStore(database, checked_metadata=False)`，保留原每次新读取。
仅受控测试显式使用 `checked_metadata=True`；当前生产 composition 不开启。
没有 HTTP/模型可写入口，未改管理员能力 flags。实际预算未通过，不能因组件通过开启。

1. 一次 metadata pass 中，每个 current record 第一次按原拥有者/namespace/id读取。
2. 重复使用该行的独立 JSON 副本。没有保存允许/拒绝、permission 或 Tool 结果。
3. 返回 pass 前，一次全新 READ COMMITTED SELECT 检查全部依赖行。
   比较完整 payload、schema、revision、存在性/墓碑；任何不同拒绝整次 pass。
   因此改回旧 payload 但 revision 增长也拒绝，不能由旧比较输入批准执行。
4. 最多256个不同 current rows，最长10秒，并叠加调用者更早的原期限。
   不持有 scope 跨用户/native UI、文件读取、模型或工具执行。
5. 历史 revision 查询仍独立读取并检查当前墓碑。原 `current_reads` 不改变行为。
6. 相同 owning task 的嵌套来源共享最终 witness；子任务独立 session/inputs。
   出错、超时、取消均清除 task-local inputs；下次 pass 全新读取。

RunnerCommands 的两轮来源谓词均保留，每轮独立初始读取和最终 witness；
OS、角色 keys、原 root、签名等外部检查仍实际调用，不缓存结果。
若 witness 发现 SQL 变动，做一次无 batch 的来源读取定位具体拒绝（例如 Run取消）；
即使新状态验证成功，仍拒绝原变动 pass。这只是诊断读，不重试 Tool/command。

EnrolledPeerRegistry 的 current/owner 接同一机制；完整原用户映射与原 actor区分不变。
SQL witness 的新增 await 之后，再观察双方实际 OS 和当前角色 keys、原期限。
原 immutable enrollment bytes 仅选择原绑定，不提供权限。新增等待期间撤销用例。
公开接口、D endpoint/watch 和原响应/原 command deadline 不变；没有开放权限。

## 已验证与限制

第一轮73实际SQL节点、最终42身份/来源节点及独立测量节点通过；需按节点去重，
不能将这些批次直接相加。所有原失败和中断证据保留。
默认关闭后44项定向回归通过；本阶段去重93个定向节点，连同历史组件回执并集245。
历史节点没有全部在最终版重跑，245不是一次全量或产品验收数字。
同一受控 channel/root/gate 的实际 SQL authority 输出相同：SELECT 42→34，
单次耗时0.180→0.140秒。它证明该组件减少查询，不代表生产整个任务的性能比例。

第二轮候选版真实 Windows 链91.23秒仍失败：command1/open0，
4临时凭据/2角色keys/child/proof pipe清理通过。首次 current 被取消，未完成一次读；
它是显式优化候选的失败，不能证明生产优化收益，也不代表默认关闭路径已重跑整链。
保留两次失败、原A10失败和候选源码摘要。内部 recheck/watch仍未装配D endpoint。
真实文件模型成果、
原拥有者认证页面、真人授权/接受与汇合全量均未据组件通过改成 accepted。
受控临时 native选择不代表本人确认，默认 flags 保持关闭。
