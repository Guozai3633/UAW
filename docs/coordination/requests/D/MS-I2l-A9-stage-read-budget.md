# A9 D：检查点、有界来源提案与独立阶段

2026-10-11。dev/runner，E:/UAW/.worktrees/runner。执行基线
ms-i2l-a9-journal-source / 225f5006f9ad246fb17816363beda4f1f1445876；
任务文档 ms-i2l-a9-journal / 22bfb00954a061a48fc3f6143593e2e91bd2c6a7。
远端标签、origin/integration 正式派发已核对，快进并 uv sync --frozen。
不消费浮动 integration。旧 MS-R2i-b 提交、失败及清理保留。

## 原检查点和必须保留的来源

| 检查点 | 所需检查 | D 当前动作 / A 需求 |
| --- | --- | --- |
| receive / actor | 当前 OS 实例/活 pipe、双角色独立 owner/actor/device/key/签名、nonce/序列与固定 connection | 保留 session.check 与 registry 主体来源，body 不授权 |
| command resolve | owning Reader 的实际固定 content Ref/版本/hash、已登记 command/device/owner、当前数据访问和签名 | 不能由收到的 command_ref 合成登记 |
| runner factory | 固定依赖、原 channel 元数据、一致 assembly | 只构造对象；改为 registry 私有 snapshot，随后 endpoint/session 与 execute 独立复查，不返回许可 |
| 第一次 current | Reader、mapping、channel、RootSnapshot、完整 authority；外部 root/key 后再次 owner/channel/authority | 建立固定比较基线，仍完整检查 |
| 私钥 await → admission | 当前设备私钥、原完整 AsyncAdmission，两次 owner/authority及外部 root/key、最后 admission CAS | 删除紧接完整 admission 前的额外 current；admission 后 current 仍与第一次绑定逐字段比较 |
| execution claim | 当前 Reader/owner/channel/root/authority，再查原本机 key/root/期限/停止，持久一次 CAS | 既有 once journal 保留；失败不撤销旧历史或产生执行许可 |
| OS open 后 | 实际打开的根/文件身份、最终路径、替换/链接/界限；等待后的当前来源与取消 | 保留 actual handle.check；不能只验输入路径 |
| OS read 后 | 同时编辑检测、UTF-8/1MiB/64KiB；当前 owner/key/root/flags/Run/request/policy/lease/fence | 无新 action；已有结果不能覆盖来源变化 |
| sign/verify 后 → signed CAS | 当前全部固定 authority/channel与本机 root/key/句柄/取消/最早期限 | 签名 await 与验证 await 后的 current 保留；原终态与 Usage 不重解释 |
| publish 后 → response | Reader数据权限、设备签名、原固定 receipt Ref/命令/attempt，当前根与channel/owner | 当前权限复查与现有 journal 不跳过 |
| 已有 journal 恢复 | owning Reader、当前数据权限/owner/channel/root/key、原签名/完整 receipt Ref | 不新 admission/reserve/dispatch/open；Run取消本身不推断正文权限撤销；unknown 不重发 |
| watch | 期限、断线/OS退出、key/owner/登记撤销；执行阶段 Run/lease/版本撤销 | 当前仍每50ms后完整 session.check，不能未接 A 来源就换为只查 OS |

## 提案：A 的有界 owning current 来源（待 A 审阅，未接运行）

建议保持公共 AsyncRunnerAuthorityPort.current 输出既有严格 RunnerAuthoritySnapshot；
A 在 owning RunnerCommands 增加内部 RegisteredRunnerRecheckPort（名称可由 A 固定）：

```
async recheck(command_ref: Ref, *, authenticated_principal: Principal,
              channel_ref: Ref) -> RunnerAuthoritySnapshot
async wait_changed(command_ref: Ref, *, authenticated_principal: Principal,
                   channel_ref: Ref, deadline: float) -> None
```

recheck 从实际 command_ref 登记行读取原完整绑定；输入没有 approved/owner/body/hash 权限声明。
需读取并核对：command/request原完整 pin及parameters；owner真实用户会话、device与双方当前key角色/撤销及原channel/proof；
Run/task/conversation及用户固定模型/model-policy；原scope/policy版本/当前取消；
Tool原spec/provider及当前provider state/revision、当前configuration pointer/flags与Run固定configuration；
原角色profile/binding revision/撤销；原ApprovalBinding完整context/action/参数/resources/decision/期限；
原预算reservation/attempt/ledger派发、cancel/overdrawn/期限；lease原holder/ref/revision/fence/有效期；
原root/workspace/grant revision/撤销/选择签名/确认期限/OS身份。
所有原引用与数据身份由 A 第一次完整准入及登记持久固定，不能从命令反推授权。

优化目标是一次有界当前读取，不是重复调用完整 owning 审批业务递归展开。
可以按 owner 独立服务执行批读；任何 await 后实际时钟及最终版本/撤销核对必须保留。
READ COMMITTED 不声称跨服务原子授权；来源不一致/缺失/新增版本/过期/撤销一律失败，不能 fallback 到旧 allowed。
输出每次均为新严格 snapshot，与 D 首次 snapshot 及固定 command 字段比较。
配置/模型/provider/审批/角色即使不在 snapshot DTO 内，也须由 A 原绑定复核并拒绝变化。
不能只返回 changed=false 或允许布尔量来代替上述当前 owning 来源。

wait_changed 必须由同一原 owning 服务持续监视上述源；返回表示失效，不能授权。
原 connection/OS/key watchdog仍独立；绝对 monotonic deadline 不重置，最晚不超原10秒响应和更早所有源期限。
若用实际SQL轮询，A应声明每次查询范围和上界；不得拿先前revision/allowed缓存作权限。
缺实时来源保持现有完整watch，默认不装配新port。生产不能接测试Event。
原普通15秒/首次90秒/root120秒/lease30秒及较早来源期限全部不变。

## 独立阶段源码与回执

本阶段仅 D runtime 工厂纯构造、read_executor 删除 admission 前重复完整 pass，及 D 测试成本测量。
无 public schema/锁/RefKind/HTTP/A源码修改。阶段源码 SHA：7395eb7fc32c3e99b46840f3432358fee38da170。
stage.xml/log：173 passed / 113.49s，无失败/错误/跳过；覆盖 read_executor、AsyncAdmission 和真实Windows读IPC，新增10项私钥 await 后变化拒绝。
Ruff与34个D源码Mypy通过。类型检查首次正确设置MYPYPATH=src;apps/local_runner。

准确基线原成功期望节点：baseline.xml/log，1 failed，83.44s，ipc_broken，command1/open0；
真实 SQL/Web/Windows双keys/双进程，native/config/审批为明确受控临时fixture，非真人或生产开关。
factory3.563s，callback24.407s，ready35.935s，assembly0.740s，审批3.147s，受控决定1.472s，
批准后调用35.686s，cleanup0.533s；GET累计耗时不与墙钟相加。
全部成本/错误/清理回执位于 ignored tests/.artifacts/D/MS-I2l-A9。
M1 后继续定向修复、实际回归；A owning来源优化与公开接口需 A 实现发布准确源码后消费。
