# 本轮可直接转发的消息

日期：2026-10-07。C/D 使用发布的 `ms-i2a`；B 的 MS-C2 已合入接受，暂无新包。消息只针对对应现有聊天，不创建新 session。

## 发给 B

```text
A 已将 UAW Session B 的 MS-C2 实现 c85bf52 和交接 c6ae25d 合入 integration；没有合并冲突。64 个组件检查、9 个真实 PostgreSQL 检查及原 8 个 Context 接线检查已通过。MS-C2 组件接受，完整 P1-02 仍待生产 authority/能力 Reader 等接线。请保留干净的 dev/context 交付边界，当前没有新的已派发包，不自动扩大范围。A 负责后续公共版本兼容；当前无需同步或重写分支。接受记录见 docs/implementation/MS-C2-acceptance.md。
```

## 发给 C

```text
开始 UAW Session C 的 MS-T2a。工作目录 E:/UAW/.worktrees/tool，分支 dev/tool。先检查工作区；干净后 git fetch origin --tags、git merge --ff-only ms-i2a，核对 HEAD 与 ms-i2a^{commit} 一致，再按新 uv.lock 同步本工作区依赖。若快进失败，保留并报告，不 reset。
阅读 docs/plan/sessions/C.md、docs/coordination/DISPATCH.md 和 docs/coordination/requests/A/MS-I2a-ports.md。实现持久 action/attempt/dispatch/effect 账本、真实 ApprovalPort/BudgetPort adapter 和 ApprovalAuthorityPort，补 SQL 重启恢复/并发/审批变化/取消/unknown 用例。公共 DTO 缺口写 C 提案交 A；不能直接改公共 schema/锁/组装/API 或其他 worker 文件。
没有真实资源 Reader、权限或 executor 就明确不可用，等待审批引用真实记录；不开放 flags，不重发未知写动作，不在持有会话事务锁时嵌套调用预算服务。完成后提交代码与 C handoff，记录实际基线 SHA、测试、缺口及 A 接线要求。MS-T2a 是本轮范围，不自动进入完整 MS-T2。
```

## 发给 D

```text
开始 UAW Session D 的 MS-R2a。工作目录 E:/UAW/.worktrees/runner，分支 dev/runner。先检查工作区；干净后 git fetch origin --tags、git merge --ff-only ms-i2a，核对 HEAD 与 ms-i2a^{commit} 一致，再按新 uv.lock 同步本工作区依赖。若快进失败，保留并报告，不 reset。
阅读 docs/plan/sessions/D.md、docs/coordination/DISPATCH.md 和 docs/coordination/requests/A/MS-I2a-ports.md。把 SignaturePort 接到公共真实 Ed25519 原语，落实可信当前 key 目录、角色/撤销及私钥保护；实现配对 nonce/一次码/挑战/RootSelection 的持久 CAS 一次使用状态，并验证真实签名篡改和并发消费。提出异步 Runner authority、可信 IPC/挑战证明及持久 DTO 接线需求。
没有可信本机确认/密钥持有证明就不批准。旧 pair.complete 不包含内联挑战证明，不能自认已验证；需要新 DTO 的提案由 A 发布公共版本。D01/D03/D06 不自行决定，测试只用独立临时目录，不开放安装/写文件/exec，不把协议测试说成真实配对完成。只改 D 允许目录；完成后提交源码和 D handoff，列真实测试与 A 接线要求。MS-R2a 是本轮范围，不自动进入完整 MS-R2。
```
