# 多 session 派发和集成记录

日期：2026-10-08。A维护。**MS-C4/MS-T2c/MS-R2c组件已接受；MS-I2f2集成范围完成。用户已报告B/C/D均同步ms-i2f2；新包MS-C5/MS-T2d/MS-R2d已发布待转发，A执行MS-I2g准备与并行接线。**

## 最近已验收的运行代码版本（ms-i2f2）

- 目录/分支：`E:/UAW` / `integration`；仓库：[Guozai3633/UAW](https://github.com/Guozai3633/UAW)。
- 已验证代码/证据提交：`9422fcaba180fdc04515c993776e7f4a09d526b2`；固定标签 **ms-i2f2** 包含随后状态记录，旧标签不移动。
- 全量 **841 passed，0 failure/error/skip**；Ruff/格式156文件，Mypy102源码文件通过。1281 schemas、272接口、26已实现公开操作。
- 新增231项检查，原610项完整重跑。[实际范围/回执](../implementation/MS-I2f2.md) 与 [接口/目录/策略](requests/A/MS-I2f2-integration.md)。
- Worker原开工基线是 `ms-i2e / ba2f3b0d9417e6d695eaa74c2f766217c98b01f1`；A原基线是 `ms-i2f1 / d3fca34528237da155617a2a86df2abcb0db86b3`。交付后再同步新版本，不中途换基线。

## 本轮接受

| Session | 原目录 / 分支 | 原源码 / handoff | A merge | 接受结果 |
| --- | --- | --- | --- | --- |
| A | E:/UAW / integration | 9422fcaba180fdc04515c993776e7f4a09d526b2 | 本分支 | MS-I2f2集成开发范围接受；完整MS-I2f/MS-I2继续 |
| B | E:/UAW/.worktrees/context / dev/context | acc68fc / 1acedb4 | 2f674ec | MS-C4组件接受；174单元＋35实际SQL通过 |
| C | E:/UAW/.worktrees/tool / dev/tool | 3d8cda3 / 3c0cd99 | 23739a1 | MS-T2c组件接受；135单元＋70实际SQL通过 |
| D | E:/UAW/.worktrees/runner / dev/runner | 38ee809 / 1e89d5c | 5b8c1ad | MS-R2c组件接受；250组件/原公共检查通过 |
| E | 未创建 | — | — | 可选、未派发 |

A另增10项跨模块SQL/组装测试，独立组件674项通过。原worker缺数据库URL/仅收集回执保持；接受依据A实跑。没有合并冲突或归属越界，没有改写worker分支、原工作区、提交或handoff，没有向其他聊天发送消息。

## A接线裁决

1. D交付的artifact回执在集成分支统一为content固定Ref；runner_receipt只是命名空间。原handoff保留，旧试验引用不提供透明别名，无新RefKind/schema。
2. Container提供实际登记命令的恢复Reader；真实SQL原命令、独立设备owner及当前密钥复查，恢复不重新准入或reserve/dispatch。
3. 可选纯计算缓存显式注入selection/formatter，默认关闭；当前权限/来源/最终复查不缓存。
4. 没有生产Tool Lookup/Reader/executor，没有Runner到Tool效果的推断映射；受控签名failed receipt不证明外部执行。公开Tool/Workspace/通用Context/Agent仍未绑定，flags仍关闭。

## 当前发包准备版本：ms-i2g-start

- 准备代码/证据提交：`ea89d30747a492c12447b8450ba28302ed262834`；固定标签 **ms-i2g-start** 包含最终派发状态记录。
- 运行源码、公共schema/ports/contracts、依赖锁及提示词相对ms-i2f2未变。本次改独立开发库脚本和分工/进度文档；A旧库兼容及8项真实SQL复验通过，B/C/D配置隔离已检查，实际库由worker自行启动。
- 841项是上个运行版本完整回执，本次没有重跑全部841项；补充验证及源码范围见[MS-I2g准备](../implementation/MS-I2g-preparation.md)。

| Session | 新包 | 范围 | 发布状态 |
| --- | --- | --- | --- |
| A | MS-I2g | 独立DB、阶段版接口、当前来源及跨模块接线 | 准备已验证，集成开发中 |
| B | MS-C5 | 通用登记/当前authority/Reader→快照→模型输入 | 原分支已同步ms-i2f2；新包文档已发布，待用户转发开工 |
| C | MS-T2d | 只读调用编排/实际text adapter/持久结果Lookup与Reader | 同上；不依赖D开发分支 |
| D | MS-R2d | 真实OS控制签名/授权根来源/装配验证 | 同上；IPC/写入exec仍在后续门槛 |
| E | 未派发 | 保持可选 | 不创建新工作区 |

每包四个连续里程碑、两个交付点；阶段版接口提交后继续同包，不等待最终集成才做后半包。具体输入输出、策略、目录和数据库命令见[发包定义](requests/A/MS-I2g-parallel-packages.md)，可转发内容见[NEXT_WAVE](NEXT_WAVE.md)。A没有替worker切分支或向其聊天发消息。

完整MS-I2f/MS-I2/MS-T2/MS-R2仍未接受，D01/D03/D06不因此改变。新包按ready_to_start记录，不把用户旧同步报告当成新包已开工。

## 当前固定公共文件摘要（与ms-i2f1相同）

| 文件 | SHA256 |
| --- | --- |
| `contracts/uaw.schema.json` | `cc5dbc6ba7bdaba40529ed196fe1249176b49967f741ecf017e40275417a8c45` |
| `src/uaw/shared/ports.py` | `fd45911eeb0e72b56459d012c4c6e8130e5d6abfabe77140bf443a8a103ba104` |
| `src/uaw/shared/contracts.py` | `08ac0c164c56c6142f3f4397bcd2c3a544e2abacc3432bf4a10d180fcb5fce7b` |
| `uv.lock` | `a065f5af348ed573e7f2547a62ec393366a499103a6e0c791686a8404b89c59f` |
| `src/uaw/resources/prompts/intent-understand-v1.txt` | `3f91702614fca270d1c8b6e3dd2842a950dbfa01685b58d5aa54cbce36114400` |

源码摘要来自实际当前文件；代码提交SHA见本页。`.gitattributes`保留字节；`.data`、私有配置/凭据、缓存、虚拟环境和worktree不进入提交。历史基线与摘要保留在Git旧标签和各实现记录。
