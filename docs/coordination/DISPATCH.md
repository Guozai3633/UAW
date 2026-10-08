# 多 session 派发和集成记录

日期：2026-10-08。A 维护。**MS-T2a / MS-R2a 组件已接受，发布 ms-i2c 供 B/C/D 在包边界同步。完整 MS-I2、MS-T2、MS-R2 与 P1-02/03/04 继续开发中。**

## 固定版本

- 目录/分支：`E:/UAW` / `integration`；仓库：[Guozai3633/UAW](https://github.com/Guozai3633/UAW)。
- 已验证代码/证据提交：`ad4ed8704cc2481ab749d1b5b16ab8284c509fd8`；固定标签 **ms-i2c** 包含随后派发状态记录。标签解析出的真实 commit 是本轮三份工作包的共同基线。
- 全量 **360 passed，0 failure/error/skip**；Ruff/格式通过（121 文件）；Mypy 89 个源码文件。1262 schema、272 接口、26 已挂载实现操作；新增内部 port 不计为新生产入口。
- 原标签 ms-i2b、ms-i2a、ms-c2-accepted、ms-i1、parallel-wave-1 保留，不移动；原 worker handoff 和提交历史保留。

## 当前接受与下一包

| Session | 本轮已接受 | 实现 / 交接 | A merge | 下一包 | 固定基线 |
| --- | --- | --- | --- | --- | --- |
| A | MS-I2c 开发集成 | 见代码提交及证据 | integration | 完整 MS-I2 公共组装继续 | ms-i2c |
| B | MS-C2 组件 | c85bf52 / c6ae25d | aa421be | **MS-C3：通用模型输入** | ms-i2c |
| C | MS-T2a 组件 | e3a19dd / 827f6ca | 3148cf1 | **MS-T2b：预算读接口与结果核对** | ms-i2c |
| D | MS-R2a 组件 | 2049c3d / 45e0f56 | 440d2fc | **MS-R2b：异步 Runner 协议** | ms-i2c |
| E | 未创建/未派发 | — | — | MS-Q1 仍可选 | 未固定 |

C 的 66 个组件用例及 17 个真实 PostgreSQL 用例已实际通过，fixture active 状态不代表联网。D 汇报范围的 100 项已由 A 复核，含真实密码学和跨进程竞争，但不等于真实配对/IPC可用。接受和兼容修复见 [MS-I2c](../implementation/MS-I2c.md)。

三个新包均只依赖已发布的 ms-i2c，不消费其他 worker 的开发分支。接口签名、严格 DTO、缺失依赖和实际实现位置见 [公共消费说明](requests/A/MS-I2c-ports.md)，完整任务见 [B](../plan/sessions/B.md)、[C](../plan/sessions/C.md)、[D](../plan/sessions/D.md)。

## 本轮转发与同步

没有向其他聊天发送消息，也没有替 worker 切换或改写分支。复制 [B/C/D 三份消息](NEXT_WAVE.md) 到对应原聊天即可开始。

| Session | 原 worktree | 原分支 |
| --- | --- | --- |
| B | E:/UAW/.worktrees/context | dev/context |
| C | E:/UAW/.worktrees/tool | dev/tool |
| D | E:/UAW/.worktrees/runner | dev/runner |

各 worker 在自己的目录确认干净后执行：

```powershell
git fetch origin --tags
git merge --ff-only ms-i2c
git rev-parse HEAD
git rev-parse 'ms-i2c^{commit}'
uv sync --frozen --extra agent-engine --link-mode copy
```

两项 SHA 应一致。快进失败保留现场并报告，不 reset。自己使用 worktree 内的缓存与临时目录，不复制凭据、私有配置或 .data。真实 SQL 使用独立测试主体；没有 URL 时提交用例给 A 实跑，不把收集成功记为通过。

## 固定公共文件摘要

以下来自代码提交 ad4ed8704cc2481ab749d1b5b16ab8284c509fd8；所有 worker 在新标签上验证。不再使用 ms-i2a 的旧摘要判断本轮公共接口。

| 文件 | SHA256 |
| --- | --- |
| `contracts/uaw.schema.json` | `b5d7cdf9df23002e6e3d3965741cbcd82b7efa34ff438b09b236e3b0b886d583` |
| `src/uaw/shared/ports.py` | `cce4db2349b92a6a2fca815917725cb7bb51fcb5ab9db86c2f456d3df2b679cd` |
| `src/uaw/shared/contracts.py` | `08ac0c164c56c6142f3f4397bcd2c3a544e2abacc3432bf4a10d180fcb5fce7b` |
| `uv.lock` | `a065f5af348ed573e7f2547a62ec393366a499103a6e0c791686a8404b89c59f` |
| `src/uaw/resources/prompts/intent-understand-v1.txt` | `3f91702614fca270d1c8b6e3dd2842a950dbfa01685b58d5aa54cbce36114400` |

共享 schema/port 的修改由 A 合入和发布。共享 typed 基础对象、锁与原文理解提示词本轮未变。保留源码字节，.data、凭据、缓存、venv、worktrees 不入库。

## 公共接线与仍未满足项

- BudgetStatePort 已有真实 SQL 实现，可从 Container.budgets 消费。当前/取消/过期恢复查询有主体和尝试校验；不授权新调用。
- pending Usage 仅币种必填，未知维度省略并保留额度；confirmed/estimated 必须完整观察记录。
- ToolReceiptReaderPort / ToolReconciliationReceipt、AsyncRunnerAuthorityPort / RunnerAuthoritySnapshot 已发布。生产 Reader 与 authority 尚未注入，测试适配器不冒充真实服务。
- ModelPrompt 已明确为 ModelInputPort 公开结果；B 不修改 Model 私有适配器，A 负责后续输入路由。
- C 后续统一消费 ExecutionPolicyPort；Tool 自己的角色、实际资源、配置、审批、预算与 executor 检查仍需保留。
- 原 pair.complete 缺真实证明仍不可用；D 的 Ticket.document 是开发签名 profile，配对 V2 留待独立公共版本。SQLite 不代替 D01 决策。
- Tool/Workspace/通用 Context Runtime 未绑定。Agent 循环、实际 LLM/可信 IPC/真实用户配对/OS密钥库实连/安装/写入/exec 均未验收。能力 flags 不开放，D01/D03/D06 保留。

## 接受历史

| 包 | Worker 提交 | A merge / 代码 | 范围 |
| --- | --- | --- | --- |
| MS-C1 | 307a49b / 0da308f | 2f0a427 | Context 首包组件 |
| MS-T1 | f9622ca / 5dd77c2 | e7b4a74 | Tool 首包组件 |
| MS-R1 | d77bf35 / 300bdf5 | c8a40d6 | Runner 首包组件 |
| MS-I1 | A | c43bbc5 / f33d162 | 222 项开发接线 |
| MS-I2a | A | ec5313b / ac9bf621 | 251 项人工审批/签名基础 |
| MS-C2 | c85bf52 / c6ae25d | aa421be / 603a0ac | 285 项时接受快照/引用组件 |
| MS-I2b | A | 27cb489 / cd43b17 | 300 项实时父子政策接线 |
| MS-T2a / MS-R2a / MS-I2c | 见当前表 | ad4ed8704cc2481ab749d1b5b16ab8284c509fd8 | 360 项组件与公共恢复接口 |

worktree 提供独立源码、HEAD 和 index，仍共享 Git 历史。端口、数据库、凭据和 OS 隔离不由聊天自动提供。继续使用原三个目录，不需要新建 session。
