# 多session派发和集成记录

此文件由A维护。开发session只写自己的handoff和提案，避免多人更新同一状态表。

日期：2026-10-07。当前：**MS-00准备完成；B/C/D分支、独立worktree及依赖已创建，首包已分配，开发聊天待用户在对应目录开启**。

## 共同代码基线

- 仓库：[Guozai3633/UAW](https://github.com/Guozai3633/UAW)，origin为`https://github.com/Guozai3633/UAW.git`。
- 集成目录/分支：`E:/UAW` / `integration`，跟踪`origin/integration`。
- 已验证代码基线SHA：`5000a0e9a6eb4cffdc21a691a916d056792d4242`；已实际推送并由远端refs核对。
- 代码基线SHA指运行代码快照；本次开工版本使用固定标签`parallel-wave-1`，包括最新派发说明。三个开发分支均从该标签对应提交开始。
- 实际开工SHA用`git rev-parse parallel-wave-1^{commit}`取得；首次开工应与本worktree的HEAD相同。标签发布后不移动；后续集成发布新版本。
- 当前全量验证：73项通过，无失败或跳过；其中13项Intent协议检查。真实PG＋受控模型响应，不证明真实LLM语义质量。
- 公开支持：20个HTTP入口＋RunRuntime.create、ModelRuntime.generate、IntentRuntime.understand/revise，共24项操作；不代表七Runtime全部完成。
- D01最终存储权威、D06真实模型和D03 Runner执行方式仍待确认/配置。
- 测试通过后Docker停止，当前不可用；环境证据注明引擎版本为此前核验。后续SQL检查需恢复Docker。
- 方案：A/B/C/D共4个session，E未创建。`dispatch_ready=true`，B/C/D首包已分配，但尚未新建开发聊天或启动编码。

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
| A | MS-00 | E:/UAW / integration | `parallel-wave-1` | 当前聊天完成开工准备 | 代码73项通过；工作区/依赖核对通过 | MS-00准备完成；继续逐包集成 |
| B | MS-C1 | E:/UAW/.worktrees/context / dev/context | `parallel-wave-1` | 首包已分配，待开启聊天 | 环境已准备；业务未开工 | 未接受 |
| C | MS-T1 | E:/UAW/.worktrees/tool / dev/tool | `parallel-wave-1` | 首包已分配，待开启聊天 | 环境已准备；业务未开工 | 未接受 |
| D | MS-R1 | E:/UAW/.worktrees/runner / dev/runner | `parallel-wave-1` | 首包已分配，待开启聊天 | 环境已准备；业务未开工 | 未接受 |
| E，可选 | MS-Q1 | 未创建 | 实际开工时固定 | 未派发 | 未开工 | 未接受 |

## 提案决定和新基线

本次A修复并接受Intent协议边界，详细范围见[实施记录](../implementation/P1-01.md)。暂无worker提案。

## 本次工作区核对

- 通过Git worktree创建三个目录，每个目录有独立HEAD、index和源码文件；共用Git历史和远端。
- 按uv.lock离线配置各自`.venv`，各安装88个锁定包；项目editable安装指向各自源码。底层Python 3.14.6安装由A管理并共用。
- 仅A在准备时使用已有依赖下载缓存；安装使用copy模式。worker后续缓存使用自己的`.cache/uv`，不更改共享缓存或锁文件。
- schema、公共port、对象、锁文件及提示词与已验证代码快照逐字节一致；虚拟环境prefix、项目来源目录、Git目录分别核对。
- 未复制`.data`、私有配置或凭据；未启动数据库、后台服务或Runner。组件首包可以使用本工作区测试fixture；实际SQL联测由A安排。

用户在各自目录新建本地聊天，粘贴[B](../plan/sessions/B.md)、[C](../plan/sessions/C.md)、[D](../plan/sessions/D.md)的开工说明。当前这三个目录已经是worktree，不必再自动生成一套；不要把三个聊天都绑定E:/UAW。

每次合入逐包审阅、组合回归并发布新集成SHA；组件包接受不自动完成原P0/P1正式验收。
