# 多session派发和集成记录

此文件由A维护。开发session只写自己的handoff和提案，避免多人更新同一状态表。

日期：2026-10-07。当前：**MS-00代码验证和Git保存已完成；独立工作区和派发尚未准备，未创建其他session/worktree**。

## 共同代码基线

- 仓库：[Guozai3633/UAW](https://github.com/Guozai3633/UAW)，origin为`https://github.com/Guozai3633/UAW.git`。
- 集成目录/分支：`E:/UAW` / `integration`，跟踪`origin/integration`。
- 已验证代码基线SHA：`5000a0e9a6eb4cffdc21a691a916d056792d4242`；已实际推送并由远端refs核对。
- 本记录在后续独立提交中补充；基线SHA指代码快照，不是本记录自身的提交SHA。
- 当前全量验证：73项通过，无失败或跳过；其中13项Intent协议检查。真实PG＋受控模型响应，不证明真实LLM语义质量。
- 公开支持：20个HTTP入口＋RunRuntime.create、ModelRuntime.generate、IntentRuntime.understand/revise，共24项操作；不代表七Runtime全部完成。
- D01最终存储权威、D06真实模型和D03 Runner执行方式仍待确认/配置。
- 测试通过后Docker停止，当前不可用；环境证据注明引擎版本为此前核验。后续SQL检查需恢复Docker。
- 方案：A/B/C/D共4个session，E可选。`dispatch_ready=false`，worker暂未派发。

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
| A | MS-00 | E:/UAW / integration | `5000a0e9` | 当前聊天完成代码准备 | 已提交/推送；73项通过 | 工作区和派发步骤待继续 |
| B | MS-C1 | 未创建 | 实际开工时固定 | 未派发 | 未开工 | 未接受 |
| C | MS-T1 | 未创建 | 实际开工时固定 | 未派发 | 未开工 | 未接受 |
| D | MS-R1 | 未创建 | 实际开工时固定 | 未派发 | 未开工 | 未接受 |
| E，可选 | MS-Q1 | 未创建 | 实际开工时固定 | 未派发 | 未开工 | 未接受 |

## 提案决定和新基线

本次A修复并接受Intent协议边界，详细范围见[实施记录](../implementation/P1-01.md)。暂无worker提案。

后续先创建独立工作区并配置各自环境，再写实际开工SHA和派发包。每次合入逐包审阅、组合回归并发布新集成SHA；组件包接受不自动完成原P0/P1正式验收。
