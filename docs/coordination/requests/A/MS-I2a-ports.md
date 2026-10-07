# A 发布：MS-I2a 消费协议和后续任务

日期：2026-10-07。新公共文件/锁/schema 一律以固定标签 `ms-i2a` 为准。工作包详见 [Session C](../../../plan/sessions/C.md)、[Session D](../../../plan/sessions/D.md)。

## C：MS-T2a，可以独立开工

1. 从组装根注入 `ApprovalPort`、`BudgetPort`，领域代码只消费公开接口。所有服务返回经过 schema 校验的业务 DTO；Tool adapter 将 DomainError 转成原有严格 ComponentResult，不伪造 wait_ref/reservation_ref。
2. 实现 `ApprovalAuthorityPort.check(request, ctx)`：从可信固定 ValidatedCall/ToolSpec 得到 effect 和规范参数 hash，验证 action 与 Run/operation、实际资源版本、当前角色、父政策交集、flags、提供方及取消。传入的摘要或模型自报 effect 不能成为权威。Reader 不可用则明确不可用。
3. 内部审批流程为：规范化并固定动作 → 当前权限/资源 → `request` 持久 pending → 用户 `decide` → `get` 当前审批 → `recheck` → 预算预留/执行前复核 → 持久调用意图 → dispatch。等待审批不持有预算；审批不自动发送。等待引用指向真实 ApprovalRequest 版本。
4. 预算方法 `reserve/dispatch/release/settle` 已有真实 SQL；每个 attempt 用原可信上下文和独占 reservation，未知用量保持待核算。不要在持有同一 conversation SQL 锁时嵌套调用 BudgetService，否则可能死锁。跨服务步骤用可恢复的阶段/幂等请求记录，不能描述为单事务。
5. 做持久 action/attempt/effect 账本及其 port、批准接线与重启恢复。没有真实 executor 继续返回不可用；claim/dispatch 后失联必须保留 unknown，不能重发写动作。公共持久 DTO 如需扩展先在 C 自有提案目录提出，A 合入后再消费。

交付要有真实 SQL 测试代码、清晰 API 样例和 restart/并发/审批变更/取消/unknown 回执；组件 fixture 不注册为产品工具。完整 MS-T2 仍待 Runner 权威与实际执行依赖。

## D：MS-R2a，可以独立开工

1. 将现有 SignaturePort 接到 `uaw.shared.runner_signatures` 的真实原语；验证前从可信当前目录读取 VerificationKey。模型/命令中的公钥、key_id/device_id 不能自证身份。每次检查撤销和角色，不能用签名验证缓存代替当前权限。
2. command 使用 control 私钥，receipt/pairing-proof/root-selection 使用设备私钥。两套密钥互不替代，私钥不得进入日志、模型上下文、普通 DTO 或仓库。
3. wire signature 为 `uaw-ed25519-v1:<key_id>:<无填充base64url签名>`；key_id 仅字母数字及 `._-`，不含冒号。被签字节由公共 helper 生成：UTF-8，JSON key 按 Python 字符串序排序，无额外空白、不做文字归一化；仅剔除顶层 signature，覆盖所有其余字段及 domain/protocol/device/key。缺字段与显式 null 不等价。
4. v1 JSON 不接受浮点、非文本 key、超过 2^53-1 的整数、超过 32 层嵌套、单对象超过 1024 项、单数组超过 4096 项或签字信封超过 2 MiB。收到的 DTO 仍先按 RunnerCommand/Receipt schema 校验，usage.attempt_id 与 command/receipt 绑定仍由消费者核对。
5. 配对 nonce/一次码/挑战及 RootSelection 采用持久 CAS 状态机：pending → 本人确认/密钥持有证明 → approved → consumed；过期/撤销不能恢复，失败/重试不能再次消费。测试限定独立临时目录。控制面存储和本机私钥/路径目录分开，最终部署存储仍待 D01。
6. 旧 pair.complete 请求没有内联挑战证明，**不能把它当作证明**。本包通过独立可信挑战/本机确认 port 的实际验证结果收敛；缺 IPC 就返回不可用。若需要网络传输证明，提案新增命名 DTO/版本，由 A 改公共 schema；不偷偷扩展旧请求。
7. 现有 AuthorityPort 是同步接口，不能用阻塞跑 async SQL 的方式接线。提出异步 authority 适配方案和可消费参数；真正发送/文件访问前复核当前 lease/fence、政策、设备/根撤销及文件句柄。此项仍是 A 的 MS-I2 汇合依赖，不以缓存 snapshot 声称已解决。

交付包括真实签名 tamper/角色/撤销测试及真实持久一次使用/CAS 测试。没有 IPC 或执行方式决定时，不接受真实配对/执行验收；安装、写入和 exec 仍禁用。

算法实现参考 [cryptography 官方 Ed25519 文档](https://cryptography.io/en/latest/hazmat/primitives/asymmetric/ed25519/)；字节规则、角色与域划分是 UAW 自己的协议，不宣称兼容第三方格式。

## A 和 B

- A 负责公共 DTO、锁、组装/迁移/API 与组合验收，集中合入 C/D 的真实权限和持久账本接口提案，继续 MS-I2；未决策项不以 fixture 绕过。
- B 按现有 MS-C2 范围继续。新审批记录不会替代 Context 来源/记忆权限；共享 schema 后续同步由 A 的固定版本通知决定。
- C/D 在原 worktree 开发，各写自身 handoff/提案；不写 A/B 文件，不自动进入完整 MS-T2/MS-R2。
