# 多 session 派发和集成记录

日期：2026-10-07。由 A 维护。当前 **B 的 MS-C2 组件已合入并接受，9 项真实 SQL 通过；B 暂无新任务。C/D 继续使用 ms-i2a 的 MS-T2a/MS-R2a 安排。完整 MS-I2 / MS-T2 / MS-R2 尚未完成。**

## 当前固定版本

- 集成目录/分支：`E:/UAW` / `integration`；仓库：[Guozai3633/UAW](https://github.com/Guozai3633/UAW)。
- 已验证集成代码/证据提交：`603a0ac4d9348dee054de0c2161bffe6e3de1cce`。包含 B/MS-C2 merge `aa421be`；本次状态元数据随后独立提交，固定标签 **`ms-c2-accepted`** 包含本次接受记录。
- C/D 新开工版本：固定标签 **`ms-i2a`**，包含上述代码与本次安排；实际整体 SHA 用 `git rev-parse 'ms-i2a^{commit}'` 核对，标签不移动。
- B 的 MS-C2 已从 **`ms-i1`** / `f33d16245619b6d446816a36b65bd5c1fc607593` 交付，合入 `ms-i2a` 后验证兼容；没有改写 B 分支。
- 旧代码 `c43bbc5`、旧标签 `ms-i1`、`parallel-wave-1` / `70f2fcc` 和最初 `5000a0e9` 均保留。
- 全量 **285 passed，0 failure/error/skip**。Ruff/格式通过；Mypy 检查 80 个源码文件。真实 PG、受控 HTTP、本机临时路径和真实 Ed25519 原语通过；不代表真实 LLM、配对、IPC 或 Runner 执行验收。
- 公开支持 22 个 HTTP 操作＋Run.create、Model.generate、Intent.understand/revise，共 26 项；七 Runtime 不因此全部完成。
- D01 最终存储权威、D03 Runner 执行方式、D06 外部模型仍待决定/配置。能力 flags 保持关闭。

## 固定文件摘要

来自已提交代码。A 修改公共契约并发布新版本后 worker 才同步，不在开发中混用不同版本。

| 文件 | SHA256 |
| --- | --- |
| `contracts/uaw.schema.json` | `e4195d1f89fb82bbc7cf5bd32e1cafdc04f44ba70a87703fc38ff65f45025b0d` |
| `src/uaw/shared/ports.py` | `8476499583ffb17ee26178405b11780164ff21a117835cd34319c69f40b05395` |
| `src/uaw/shared/contracts.py` | `08ac0c164c56c6142f3f4397bcd2c3a544e2abacc3432bf4a10d180fcb5fce7b` |
| `uv.lock` | `a065f5af348ed573e7f2547a62ec393366a499103a6e0c791686a8404b89c59f` |
| `src/uaw/resources/prompts/intent-understand-v1.txt` | `3f91702614fca270d1c8b6e3dd2842a950dbfa01685b58d5aa54cbce36114400` |

上述公共摘要仍为 ms-i2a：当时新增 ApprovalBinding、收紧 RunnerReceipt 互斥分支、增加审批/预算 ports 和 crypto 锁。此次 MS-C2 合入没有再改公共文件、原文、用户模型政策、提示词或能力开关。

## 下一轮安排

| Session | 目录 / 分支 | 当前任务 | 基线 | 本轮交付 |
| --- | --- | --- | --- | --- |
| A | `E:/UAW` / `integration` | MS-I2 继续 | 当前集成分支 | 审阅公共提案、接当前权限/持久调用/Runner authority，逐包合入和组合验收 |
| B | `E:/UAW/.worktrees/context` / `dev/context` | **MS-C2 组件已接受，暂无新包** | 已交付自 `ms-i1` | 实现 `c85bf52` / 交接 `c6ae25d`；A merge `aa421be`；9 项 SQL 实际通过 |
| C | `E:/UAW/.worktrees/tool` / `dev/tool` | **MS-T2a，开工说明已准备** | `ms-i2a` | 持久 action/attempt/effect 账本、真实审批/预算 adapter、SQL 恢复与并发测试 |
| D | `E:/UAW/.worktrees/runner` / `dev/runner` | **MS-R2a，开工说明已准备** | `ms-i2a` | 真实签名 adapter、当前 key 撤销、配对/RootSelection 持久 CAS，一次使用测试 |
| E | 未创建 | MS-Q1 未派发 | 未固定 | 可选样本，不阻塞本轮 |

**本轮通过文档发布安排，没有向其他聊天发送消息或替 worker 切换分支。** 将 [C 的开工说明](../plan/sessions/C.md) / [D 的开工说明](../plan/sessions/D.md) 转发到对应现有聊天即可；可直接复制 [本轮转发消息](NEXT_WAVE.md)。

C/D 先核对工作区干净，随后在各自目录同步：

```powershell
git fetch origin --tags
git merge --ff-only ms-i2a
git rev-parse HEAD
git rev-parse 'ms-i2a^{commit}'
uv sync --frozen --extra agent-engine --link-mode copy
```

两项 SHA 应一致。快进失败先保留并报告，不 reset；后续下载使用各自 `.cache/uv`，不修改锁或 A 的缓存。新包只同步源码/依赖，不复制 `.data`、私有配置、凭据或数据库 URL。真实 SQL 联测由 A 安排独立测试主体，worker 提交真实测试代码也可交 A 运行。

MS-T2a/MS-R2a 不互相依赖，B 的 MS-C2 已独立接受。A 可以在任一包完成后独立审阅；存在接口依赖的汇合才等待对应包。完整 MS-T2/MS-R2 的真实执行仍等待 MS-I2，不因子包开工自动解锁。

## 公共接线和未满足项

- 审批：真实 SQL 人工单次决定和认证 get/decide/recheck 已实现；默认没有 Tool 动作权限 adapter，批准/创建仍拒绝。assisted/automatic、规则评估、父政策链和持续授权明确不可用。
- 预算：已有真实 SQL 服务和公共 port。C 使用持久阶段、幂等请求恢复跨服务步骤，不嵌套持有同一会话锁。
- Runner：真实 Ed25519 原语和回执互斥规则已发布；D 落实当前可信 key、一次码/挑战/本机确认和持久仓储。没有真实证明/IPC不能认为用户已配对。
- A 负责 Runner 异步 authority 与实际 lease/fence/取消/撤销接线；不使用短期缓存快照替代执行前当前状态检查。
- Tool/Workspace 公共 Runtime 仍未绑定。没有真实 executor 时保持不可用；不开放安装、写文件或 exec。
- 详细消费方式见 [MS-I2a ports](requests/A/MS-I2a-ports.md)，实现/验证见 [MS-I2a](../implementation/MS-I2a.md)。
- MS-C2 的持久快照/引用仓储与 ports 已接受；通用 CompositionAuthority、真实能力 Reader、purpose 规则/保护/epoch 所有者及通用 Model 输入仍待接线，Context 公共 Runtime 未绑定。详情见 [接收决定](requests/A/MS-C2-integration.md) 与 [组件接受](../implementation/MS-C2-acceptance.md)。

## 首波接受历史

| Session / 包 | Worker 提交 | A merge | 接受范围 |
| --- | --- | --- | --- |
| B / MS-C1 | `307a49b` / `0da308f` | `2f0a427` | Context 组件接受，完整 P1-02 仍开发中 |
| C / MS-T1 | `f9622ca` / `5dd77c2` | `e7b4a74` | Tool 组件接受，完整 P1-03 仍开发中 |
| D / MS-R1 | `d77bf35` / `300bdf5` | `c8a40d6` | Runner 协议组件接受，完整 P1-04 仍开发中 |
| A / MS-I1 | `c43bbc5`；发布 `f33d162` | 已在 integration | 222 项通过的开发范围；真实语义/执行未验收 |
| A / MS-I2a | `ec5313b` | 已在 integration | 251 项通过的公共基础；完整 MS-I2 未验收 |
| B / MS-C2 | `c85bf52` / `c6ae25d` | `aa421be` | 64 个组件＋9 个真实 SQL 用例通过；完整 P1-02 仍开发中 |

首包原 handoff 保留，不替 worker 改写回执。本次只更新 A 的集成 checkout；三个原 worker 目录在发布前检查均无未提交改动，没有替它们 merge、重建或删除工作区。

worktree 提供独立 HEAD/index/源码；仍共用 Git 历史，不代表 OS 沙箱、端口、数据库和系统凭据自动隔离。继续使用原三个目录，无需创建新会话或新工作区。
