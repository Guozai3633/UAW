# A9 原只读链响应预算修复请求（未派发）

2026-10-11。A 仍在自己的 integration 接线；D 不消费浮动 HEAD。
开工源码需由 A 另行发布准确阶段 SHA，本页不是新包或 accepted 记录。

## 实际失败

原测试 `test_a8_file_facade_approval_budget_actual_helper_read` 未改断言或时限。
A 已消费 D `acd7bd9d10387566c634b87d99fe3c01c165f618`。
最近回执 `tests/.artifacts/A/MS-I2l/a9-source12.xml`：103.47 秒，
原 Tool 返回 `ipc_broken`，发送 command 1 次，打开文件 0 次；
4 个随机凭据已清理、2 个角色 key 已撤销、原子进程退出、proof pipe 关闭。
此前 source2–source11、原失败诊断均保留，不能将来源组件通过当实际文件链通过。

原执行路径中，端点 dispatch 的多个步骤又进入
`ReadOnlyRunner.current`；该方法同时展开 journal resolve、owner、channel、root、
两次完整 async authority。authority 再进入 A `RunnerCommands.collect`，
每次 collect 有两次完整 Tool 审批/角色/配置/模型/预算/lease/root/device 复查。
此外 watch 每 50ms 触发完整 session 当前来源。真实 SQL 接线后形成重复展开。
这不是已确认的单一 D bug：A 注册/发送前的展开也占用原 30 秒 lease，需一起压缩。

## D 负责的具体审阅

1. 给原 read endpoint/runner 定义每个检查点真正需要的来源，并区分原完整准入、
   等待后的当前变化检查、OS 文件句柄/根/签名复查和已有回执的数据读取权限。
   保持独立 owning 来源；不得用上一次 allowed 代替当前权限。
2. 提出可由 A 提供的有界当前来源 port；若需要批读取/版本核对，要精确列明
   读哪些来源、原完整绑定、输出结构、期限和变更失败。不得从 command/body 自报授权。
3. watch 需在原取消/断连/撤销/期限内停止实际工作；避免与 dispatch 无间隔重复展开
   同一完整链。不要删除关键等待后的检查来满足耗时。
4. 原测试在准确 A 阶段上复跑；必须实际一次打开并核对原 signed journal/recovery。
   执行中 root/key/owner/role/config/provider/Run cancel/lease/fence 变化仍应拒绝。
   所有失败、次数与清理回执保留。

## A 负责的配合

A 保留 provider/Run 原准入、权限/审批 owning service、控制签名和实际 SQL 适配。
A 负责精简原命令 register 后没有等待的重复 collect，以及登记到发送前的来源展开。
任何新的来源 port 都先明确契约，再由双方各自实现；A 不修改 D 业务源码或分支。

A随后已补充`InstalledJournalRecovery`：首次仍原command单次发送；后续原材料
通过实际ReadExecutionJournal发布Ref及ReceiptJournal读取并验证原签名。
不会向D已进入回执后等待的同一连接再次发送recover。仍需原当前owner/device/channel/root
与数据权限；已关闭或撤销的旧通道不自动重连。6个实际SQL/SQLite/签名组件节点通过，
不能证明首次Windows读取通过。新源码准确SHA由DISPATCH的journal续项发布。

## 不变门槛

不增加原 10 秒 frame/response、15 秒普通启动、90 秒首次、120 秒根窗口、
30 秒 lease 或任何较早来源期限；不重发 unknown；不自动开 flags。
受控 native/审批仅组件验证，不等于本人确认。没有新用户文件或模型调用。
