# 多session派发和集成记录

此文件由A维护。开发session只写自己的handoff和提案，避免多人更新同一状态表。

日期：2026-10-07。当前：**B/C/D首包组件已分别合入并接受；MS-I1开发范围通过，B同步新基线后执行MS-C2。A继续MS-I2；MS-T2/MS-R2尚未派发。**

## 共同代码基线

- 仓库：[Guozai3633/UAW](https://github.com/Guozai3633/UAW)，origin为`https://github.com/Guozai3633/UAW.git`。
- 集成目录/分支：`E:/UAW` / `integration`，跟踪`origin/integration`。
- 新验证代码SHA：`c43bbc5a87dc244a918aa835032ed491e7e2f421`，包含三份组件和MS-I1接线。
- 新开工版本为固定标签`ms-i1`，包含上述代码与本次派发说明；实际整体SHA用`git rev-parse 'ms-i1^{commit}'`取得。标签不移动，后续另发新版本。
- 第一波历史版本仍是`parallel-wave-1` / `70f2fcccb88650c616920a5630d2caa45d94ad45`；原73项验证代码为`5000a0e9a6eb4cffdc21a691a916d056792d4242`，均保留。
- 最终全量验证：222项通过，0失败/错误/跳过。使用真实PG、本机临时路径/junction与受控HTTP回复；不证明真实LLM语义质量或Runner执行。
- 公开支持：20个HTTP入口＋RunRuntime.create、ModelRuntime.generate、IntentRuntime.understand/revise，共24项操作；不代表七Runtime全部完成。
- D01最终存储权威、D06真实模型和D03 Runner执行方式仍待确认/配置。
- 本轮Docker与PG实际可用，环境版本现场读取；JUnit和源码/环境摘要已更新。回归脚本也覆盖实际Runner模块的静态/类型检查。
- 方案：A/B/C/D共4个session，E未创建。三位worker均已交付；A只更新integration，不替worker改写分支或工作文件。

## 固定文件摘要

来自已提交的代码快照。共享接口变更由A合入，并发布新版本后由worker同步。

| 文件 | SHA256 |
| --- | --- |
| `contracts/uaw.schema.json` | `c9737069f74331ee5f519eabc1a8bf5c2527389da0e922d46ba892557b522a2c` |
| `src/uaw/shared/ports.py` | `857ba50e7a74439ce4c266a4193c09271eabf4dde87232591a9d80826f21e490` |
| `src/uaw/shared/contracts.py` | `08ac0c164c56c6142f3f4397bcd2c3a544e2abacc3432bf4a10d180fcb5fce7b` |
| `uv.lock` | `e048aafdcfdd0949b7234a8d381fa0dd1d13450ee70f13b5e01c70b79156f9f4` |
| `src/uaw/resources/prompts/intent-understand-v1.txt` | `3f91702614fca270d1c8b6e3dd2842a950dbfa01685b58d5aa54cbce36114400` |

`.gitattributes`保留源码字节，避免不同机器的换行转换使来源/证据摘要漂移。`.data`、私有配置、凭据、虚拟环境、缓存及worktree未进入提交。

## 分派与接受

| Session | 首个准备包 | 实际工作区/分支 | 基线SHA | 派发 | 提交SHA/回执 | 接受结果 |
| --- | --- | --- | --- | --- | --- | --- |
| A | MS-00 / MS-I1 | E:/UAW / integration | `ms-i1` | 接线已完成；继续MS-I2 | `c43bbc5`；最终222项通过，静态/格式/75文件类型检查通过 | MS-I1开发范围接受；完整P1未验收 |
| B | MS-C1 | E:/UAW/.worktrees/context / dev/context | 首包`parallel-wave-1` | MS-C2已派发；同步`ms-i1`后开始 | `307a49b` / `0da308f`；A merge `2f0a427` | 组件接受；P1-02开发中 |
| C | MS-T1 | E:/UAW/.worktrees/tool / dev/tool | 首包`parallel-wave-1` | MS-T2等待MS-I2，未派发 | `f9622ca` / `5dd77c2`；A merge `e7b4a74` | 组件接受；P1-03开发中 |
| D | MS-R1 | E:/UAW/.worktrees/runner / dev/runner | 首包`parallel-wave-1` | MS-R2等待MS-I2，未派发 | `d77bf35` / `300bdf5`；A merge `c8a40d6` | 组件接受；P1-04开发中 |
| E，可选 | MS-Q1 | 未创建 | 实际开工时固定 | 未派发 | 未开工 | 未接受 |

## 提案决定和新基线

三个首包无归属越界、无合并冲突；逐包保留merge提交。详情见[MS-I1实施记录](../implementation/MS-I1.md)。

- B接线提案按理解专用范围采用：真实Run来源/当前政策/取消、单个平台规则、固定模型窗口；Intent与Model共用一个resolver。通用Composer、项目/技能规则、预览仍明确不可用。
- C目录/参数/身份与预检复核port采用；Model输出的工具RefKind已统一为configuration并实际验证能进入normalize。真实预算/审批/持久dispatch/effect/settle尚未注入。
- D命令/根/回执组件采用；真实签名/IPC/配对/持久仓储及文件句柄执行尚未注入。回执互斥schema提案仍待MS-I2，不自行更改公共DTO。
- [A的接口消费与提案决定](requests/A/MS-I1-adapters.md)记录准确文件和限定范围。没有修改原固定公共文件、依赖锁、迁移或能力flags。

## 下一轮

**B / MS-C2已派发**。沿用原worktree，在干净的dev/context中同步整体开工版本：

```powershell
git fetch origin --tags
git merge --ff-only ms-i1
git rev-parse HEAD
git rev-parse 'ms-i1^{commit}'
```

同步后两项SHA相同。若存在新的本地改动/提交使快进失败，先保留并报告，不reset。B阅读A接线说明后，在自有composer/repository/references及测试目录开发固定快照与引用查询；不改A的理解专用builder或新adapter。

**A / MS-I2继续；C / MS-T2和D / MS-R2未派发。** 本轮已完成C/D组件审阅与合入，MS-I2剩余工作是发布真实预算/审批/持久调用及Runner权威port，统一回执/配对协议并验证消费方；单凭本次合并不足以开放下一包的真实执行。C/D保留干净交接边界，待新固定MS-I2版本再同步。

## 本次工作区核对

- 通过Git worktree创建三个目录，每个目录有独立HEAD、index和源码文件；共用Git历史和远端。
- 按uv.lock离线配置各自`.venv`，各安装88个锁定包；项目editable安装指向各自源码。底层Python 3.14.6安装由A管理并共用。
- 仅A在准备时使用已有依赖下载缓存；安装使用copy模式。worker后续缓存使用自己的`.cache/uv`，不更改共享缓存或锁文件。
- schema、公共port、对象、锁文件及提示词与已验证代码快照逐字节一致；虚拟环境prefix、项目来源目录、Git目录分别核对。
- 未复制`.data`、私有配置或凭据；未启动数据库、后台服务或Runner。组件首包可以使用本工作区测试fixture；实际SQL联测由A安排。

沿用[B](../plan/sessions/B.md)、[C](../plan/sessions/C.md)、[D](../plan/sessions/D.md)的原三个独立worktree；无需再创建一套。会话/目录隔离仍不等于OS沙箱，也不自动隔离端口、数据库或系统凭据。

每次合入逐包审阅、组合回归并发布新集成SHA；组件包接受不自动完成原P0/P1正式验收。
