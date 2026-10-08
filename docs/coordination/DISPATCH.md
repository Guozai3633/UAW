# 多 session 派发和集成记录

日期：2026-10-08。A维护。**MS-C3 / MS-T2b / MS-R2b 组件已接受；MS-I2e 集成范围完成。用户已确认 B/C/D 同时开工，基线固定 ms-i2e；A的 MS-I2f1 组件已验收，完整 MS-I2f 继续开发。**

## 当前集成版本

- 目录/分支：`E:/UAW` / `integration`；仓库：[Guozai3633/UAW](https://github.com/Guozai3633/UAW)。
- 已验证代码/证据提交：`98ea1ce2a4512f48dd6a4465ff15a83e003dc9c6`；固定标签 **ms-i2f1** 包含随后状态记录，旧标签不移动。
- 全量 **610 passed，0 failure/error/skip**；Ruff/格式142文件、Mypy98源码文件通过。1281 schemas、272接口、26已实现操作。
- 本次新增47项真实SQL/签名组件检查；原563项完整重跑。[MS-I2f1实际范围](../implementation/MS-I2f1.md) 与 [接口/目录/策略](requests/A/MS-I2f1-scope.md)。
- B/C/D开发中的共同基线仍为 `ms-i2e / ba2f3b0`，不要求中途消费 A 新对象/port；后续包边界才同步新版本。

## 本轮接受

| Session | 原目录 / 分支 | 已交付源码 / handoff | A merge | 接受结果 |
| --- | --- | --- | --- | --- |
| A | E:/UAW / integration | 98ea1ce2a4512f48dd6a4465ff15a83e003dc9c6 | 本分支 | MS-I2f1开发组件接受；完整MS-I2f/MS-I2继续 |
| B | E:/UAW/.worktrees/context / dev/context | 396b548 / 00332fc | 0d6521d | **MS-C3组件接受**；原15项SQL已由A实跑 |
| C | E:/UAW/.worktrees/tool / dev/tool | c78d371 / 3c76bb2 | daaae658 | **MS-T2b组件接受**；97单元＋43实际SQL通过 |
| D | E:/UAW/.worktrees/runner / dev/runner | 5b97247 / 76fbb36 | 38492df | **MS-R2b组件接受**；172项组件/原公共回归通过 |
| E | 未创建 | — | — | 可选、未派发 |

C 的 140 项本轮实际复验包含原用例，不当作140项新增。相比ms-i2d新增31项单元＋26项SQL，全量506＋57＝563。A修复SQL测试与单元测试同名造成的跨目录收集冲突，没有修改C业务行为。原worker缺连接/仅收集回执仍保留，实际接受见 [MS-I2e](../implementation/MS-I2e.md) 和 [MS-I2d](../implementation/MS-I2d.md)。

没有合并冲突，没有改写worker原worktree、分支、提交或handoff。没有向其他聊天发送消息；任务通过[可转发说明](NEXT_WAVE.md)发布。

## 下一轮派发

| Session | 包 | 目标 | 固定开工标签 | 状态 |
| --- | --- | --- | --- | --- |
| A | MS-I2f1 / 完整MS-I2f | 设备/请求/命令登记、当前权威组件；真实来源接线另验收 | ms-i2e | MS-I2f1组件接受；完整包继续 |
| B | MS-C4 | 上下文纯计算有界缓存，每次仍校验当前权限/来源 | ms-i2e | 用户已确认开工 |
| C | MS-T2c | ToolFacade核对入口、可信查找和明确outcome读取 | ms-i2e | 用户已确认开工 |
| D | MS-R2c | 签名终态回执持久journal与当前来源恢复读取 | ms-i2e | 用户已确认开工 |
| E | MS-Q1 | 可选三类样本/验收标准 | 尚未派发 | 不创建新工作区 |

精确输入/输出、内部port、目录、策略与必要验证见 [MS-I2e下一轮契约](requests/A/MS-I2e-next-packages.md)。三个worker包仅依赖已合入ms-i2e，互不读取开发分支。A逐包接受，不必等所有worker同时完成；开发中的worker保留自己固定基线。

包定义源见 `planning/parallel_catalog.py` 的 PACKAGES；文件归属见 `docs/plan/sessions/`。A 子包的接口、来源、目录、链路和退出条件见 [MS-I2f1详细范围](requests/A/MS-I2f1-scope.md)。D 当前包使用现有 `content` Ref，`runner_receipt` 只表示命名空间；这是文字勘误，不需换基线或新增私有枚举。

工作区干净后自行fetch并`git merge --ff-only ms-i2e`，核对HEAD与标签commit相同，再同步锁；失败报告，不reset/rebase或拿共享文件单独覆盖。A不替worker执行同步或改写分支。公共schema/port/依赖/迁移由A统一发布，worker在自己的requests目录提案。

## 公共消费与仍未开放的能力

- `Container.execution_leases`已有实际PostgreSQL根租约服务；当前holder/session、CAS、单调fence、到期/撤销终态和清理通过。lease不授予设备/文件/工具权限。
- ModelInput按真实binding命名空间路由；generic缺authority/Reader不退回理解模板，生产通用Composer仍未就绪。
- ToolBudgetAdapter必须显式注入`state=Container.budgets`；ToolApprovalAuthority必须注入`policies=Container.execution_permissions`，缺port无私有表回退。
- ToolReconciler消费实际固定回执/证据；confirmed与核对ok不代表applied，费用独立。生产Lookup/Reader/executor仍缺，公开Tool/Workspace/通用Context仍未绑定。
- 设备/原请求/命令登记与异步当前权威组件已有内部服务；真实channel/root/current role-resource-consent/control signing后端及IPC、最终fence/撤销消费协调仍待A接线。现有admission和本地journal不证明跨服务原子执行。
- 真实Provider、配对、OS凭据实连、安装/写入/exec和Agent闭环未验收；flags保持关闭，D01/D03/D06及原P1阶段门槛保留。

## 开发中worker固定公共文件摘要（ms-i2e，来自 8278a5aa7b47df0b35765cfce4d2b4eb43db0c97）

| 文件 | SHA256 |
| --- | --- |
| `contracts/uaw.schema.json` | `45161b36f2e81622e73f86c23b048cda8d55686e7045248f0394ab51d13dbe6b` |
| `src/uaw/shared/ports.py` | `453cd9cd21b92a77c6e370fc6f0463072a3903a2c6b5beee56dec4f93b0c27a5` |
| `src/uaw/shared/contracts.py` | `08ac0c164c56c6142f3f4397bcd2c3a544e2abacc3432bf4a10d180fcb5fce7b` |
| `uv.lock` | `a065f5af348ed573e7f2547a62ec393366a499103a6e0c791686a8404b89c59f` |
| `src/uaw/resources/prompts/intent-understand-v1.txt` | `3f91702614fca270d1c8b6e3dd2842a950dbfa01685b58d5aa54cbce36114400` |

`.gitattributes`保留源码字节；`.data`、凭据/私有配置、虚拟环境、缓存和worktree不进入提交。上表固定到worker的ms-i2e；A在ms-i2f1新增13个命名对象与内部port，原端口保留，锁/提示词/公共contracts.py未变。worker不从A工作目录零散复制新文件，原包交付后再统一同步。

## ms-i2f1 新公共快照（来自 98ea1ce2a4512f48dd6a4465ff15a83e003dc9c6）

| 文件 | SHA256 |
| --- | --- |
| `contracts/uaw.schema.json` | `cc5dbc6ba7bdaba40529ed196fe1249176b49967f741ecf017e40275417a8c45` |
| `src/uaw/shared/ports.py` | `fd45911eeb0e72b56459d012c4c6e8130e5d6abfabe77140bf443a8a103ba104` |
| `src/uaw/shared/contracts.py` | `08ac0c164c56c6142f3f4397bcd2c3a544e2abacc3432bf4a10d180fcb5fce7b` |
| `uv.lock` | `a065f5af348ed573e7f2547a62ec393366a499103a6e0c791686a8404b89c59f` |
| `src/uaw/resources/prompts/intent-understand-v1.txt` | `3f91702614fca270d1c8b6e3dd2842a950dbfa01685b58d5aa54cbce36114400` |
