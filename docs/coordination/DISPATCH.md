# 多 session 派发和集成记录

日期：2026-10-08。A维护。**MS-I2g实际来源与装配开发中。B/C/D阶段版已分别合入；C/MS-T2d和D/MS-R2d已按最终组件范围接受，B/MS-C5继续后半包。上一完整运行回执仍为ms-i2f2。**

## A当前已验证阶段版本：ms-i2g-a1

- 源码/证据提交：**8b581af6eca951a2af2919361feaaeb85afa2477**；固定阶段标签ms-i2g-a1包含随后状态记录，不移动ms-i2g-start或旧集成标签。
- A当前来源/内部装配与C/D最终组件接受完成。234/41/27三个实际批次去重268项通过；Ruff/格式186文件/Mypy117源码通过。详见[实际范围](../implementation/MS-I2g-A1.md)及[方法/输入输出/策略](requests/A/MS-I2g-wiring.md)。
- 该阶段不是完整MS-I2g里程碑，历史全量841仍属于ms-i2f2。B继续固定ms-i2g-start完成MS-C5；C/D本包无需重做，下一包未派发。没有代替worker切分支、合并或发聊天消息。
- 新增RunToolAccessBinding及其文档/资源副本；旧请求/响应、shared ports/contracts、uv.lock不变。当前schema/hash以environment.json和该阶段标签为准。

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
| A | MS-I2g | 当前Run/固定模型/角色/结果数据权限与跨模块装配 | 源码72abb2b＋后续接线，受影响和跨模块验证；完整里程碑待B最终回执 |
| B | MS-C5 | 通用登记/当前authority/Reader→快照→模型输入 | 阶段d0ad58f合入80b86b7；174单元＋7真实SQL回执，最终包未接受 |
| C | MS-T2d | 只读调用编排/实际text adapter/持久结果Lookup与Reader | 阶段717c237合入e1503dc；最终859f5d0/db09a69合入5721ad4；162单元＋100不同SQL按组件范围接受 |
| D | MS-R2d | 真实OS控制签名/授权根来源/装配验证 | 阶段1287a05合入0be96be；最终7d946de/366c916合入b735407；326项通过，OS passed/cleaned；按组件范围接受 |
| E | 未派发 | 保持可选 | 不创建新工作区 |

C 的100个SQL是首轮原70＋最终新增30的不同通过节点覆盖，不是一次100项运行；首轮新增测试decline枚举错误已修复并完整复跑新增路径，原失败回执保留。D 的326项是worker实际模块/原共享回归，A不重新接管全模块执行。具体接线见 [MS-I2g当前来源](requests/A/MS-I2g-wiring.md)。完整P1、真实LLM/IPC/用户确认/执行仍未验收，flags未开放。

每包四个连续里程碑、两个交付点；阶段版接口提交后继续同包，不等待最终集成才做后半包。具体输入输出、策略、目录和数据库命令见[发包定义](requests/A/MS-I2g-parallel-packages.md)，可转发内容见[NEXT_WAVE](NEXT_WAVE.md)。A没有替worker切分支或向其聊天发消息。

完整MS-I2f/MS-I2/MS-T2/MS-R2仍未接受，D01/D03/D06不因此改变。B按in_progress、C/D按accepted_component记录；不把局部组件接受提升为整轮产品接受。

## Worker开工基线固定公共文件摘要（ms-i2g-start）

以下是worker本轮固定基线的字节，不是新增RunToolAccessBinding后的A阶段schema；A当前摘要见environment.json。

| 文件 | SHA256 |
| --- | --- |
| `contracts/uaw.schema.json` | `cc5dbc6ba7bdaba40529ed196fe1249176b49967f741ecf017e40275417a8c45` |
| `src/uaw/shared/ports.py` | `fd45911eeb0e72b56459d012c4c6e8130e5d6abfabe77140bf443a8a103ba104` |
| `src/uaw/shared/contracts.py` | `08ac0c164c56c6142f3f4397bcd2c3a544e2abacc3432bf4a10d180fcb5fce7b` |
| `uv.lock` | `a065f5af348ed573e7f2547a62ec393366a499103a6e0c791686a8404b89c59f` |
| `src/uaw/resources/prompts/intent-understand-v1.txt` | `3f91702614fca270d1c8b6e3dd2842a950dbfa01685b58d5aa54cbce36114400` |

基线摘要来自ms-i2g-start的实际文件；代码提交SHA见本页。`.gitattributes`保留字节；`.data`、私有配置/凭据、缓存、虚拟环境和worktree不进入提交。历史基线与摘要保留在Git旧标签和各实现记录。
