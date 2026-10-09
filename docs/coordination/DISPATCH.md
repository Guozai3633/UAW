# 多 session 派发和集成记录

## 当前安排：MS-I2i（2026-10-09）

- 固定开工标签 **ms-i2i-start**；运行来源 **ms-i2h-a3 / 3e5917d9b8dffa767f403c3d71a1884327db8f70**。本次准备完整分包和目录，不新增Runtime执行能力，保留上轮真实13调用/31聚焦及历史全量1077回执。
- A/MS-I2i：当前固定模型评估、文本/Markdown成果、逐项校验与完成控制；B/MS-C7：Context提速/批读/来源等价；C/MS-T2f：两个办公纯数据工具和多适配器恢复；D/MS-R2f：Windows真实双进程IPC及只读临时根链。
- 状态均为**已发布待开工**，不等于已实现/接受。各包M1尽早交接口，M2阶段源码后继续M3/M4，A阶段SHA到即审阅并逐包合入；worker实跑模块SQL，A做受影响/跨模块，最终里程碑一次全量。
- 原B/C/D目录和分支已只读核对，三个工作区干净；当前HEAD分别1cd90da/94c7506/7d6ee06，需worker自行fetch/快进到新标签。A未修改worker分支/工作区，也未发其他聊天消息。新包不依赖其他worker开发分支，纯数据交付不等待D。
- [全部接口/输入输出/策略/目录/四里程碑](requests/A/MS-I2i-parallel-packages.md)、[四份可转发消息](NEXT_WAVE.md)、[准备记录](../implementation/MS-I2i-preparation.md)。批读A适配在B阶段签名到达后优先交付；原兼容路径可独立继续，缺批读不冒充优化成功。用户模型/原文/版本/权限/取消保持；本机flags、写入/安装/exec及未决定的正式部署不因派发开放。
- 代码准备提交、固定标签SHA及远程状态在发布步骤记录，旧标签不移动。

## 历史运行阶段（以下记录保留）

## 当前阶段：MS-I2h-A3（2026-10-09）

- 用户指定DeepSeek-V4.1-Flash并给受保护凭据句柄；真实GET模型清单、ModelRuntime、Intent及根循环已验。13次调用含原失败，三个最终有界样例通过；原文和固定模型保留，费用pending。
- 31不同聚焦检查通过；Ruff/233格式/Mypy141源码通过，历史全量1077不重写。修复来源定位和根输出额度，严格JSON拒绝与简短必填提示保留。
- [阶段记录](../implementation/MS-I2h-A3.md)、[回执](../implementation/evidence/ms-i2h-a3.json)。专业成果、生产认证/IPC/用户确认、多规则实际评估器及embedding仍待验；flags/公开入口未开放。
- 代码/证据提交20bb296052417743673fcb0b906226b79f5cbeb0；固定阶段标签ms-i2h-a3包含后续状态记录，远程按实际push/ls-remote核对。B/C/D组件接受保持，下一包未派发。

## 历史阶段：MS-I2h-A2（2026-10-09）

- B/MS-C6、C/MS-T2e、D/MS-R2e已审阅并按组件接受；正常merge分别2969551/32961fd/cb087d0，无冲突，worker分支/提交未改。
- 原始回执和来源字节已复核：B351、C342、D431通过；C失败与复跑、D真实Windows回执及cleaned保留，计数不累加成产品进度。
- A去重421个聚焦节点通过，首次失败与修复保留；Ruff/228格式/Mypy138源码通过。多规则组装、检索→固定模型→可见工具定义、JSON-object及64KiB本机读取已验证。完整1077仍属于ms-i2g，完整MS-I2h/P1未接受。
- 精确修正：检索最多32候选；重要正文不会因相同语义标签被丢弃；仅FileContent扩至65536字符，通用Text16384及返回64KiB字节上限保留。
- [阶段范围](../implementation/MS-I2h-A2.md)、[A证据](../implementation/evidence/ms-i2h-a2.json)、[worker复核](../implementation/evidence/ms-i2h-worker-receipts.json)。真实DeepSeek凭据/模型名待用户提供，隐藏录入与协议要求见[此处](../implementation/DEEPSEEK_ACCEPTANCE.md)。实际固定Model规则评估器、真实embedding、IPC/用户确认、Tool文件结果和专业交付尚待后续；flags及公开绑定未变。
- 已验证代码/证据提交：**14f844253ab3ddc3b1366fa989e5c1cb7a3573ef**；固定阶段标签 **ms-i2h-a2** 包含随后状态记录。atomic推送后按ls-remote核对integration及标签，远程结果以实际命令回执为准。worker开工ms-i2h-start不移动，下一包未派发。

## 历史阶段（以下记录保留）

## 当前阶段：MS-I2h-A1（2026-10-09）

- A根实例/固定用户模型/有限步动态循环开发组件接受；23单元＋12 Agent SQL＋1原Model兼容SQL，去重36项通过，无最终失败/错误/跳过。最后两项含一个重复未知调用节点，聚合选用最新结果。Ruff/209格式/Mypy131源码通过。
- 真正的Context→Model→审批/预算→text→观察→下一模型输入，以及取消/未知调用恢复/真实PG图检查点已验证。实际上下文纪元来自固定快照，不用Agent步数代替。
- [实际范围与失败修复](../implementation/MS-I2h-A1.md)、[目录/签名/状态链](requests/A/MS-I2h-Agent-wiring.md)、[去重证据索引](../implementation/evidence/ms-i2h-a1.json)。公开绑定、flags和共享port/依赖锁不变；真实LLM/专业交付与产品整轮仍未接受。
- 上次完整开发集成仍是ms-i2g / 1077；A阶段回执不冒充当前全量。完整MS-I2h在worker合入后的里程碑执行。
- 已验证代码/证据提交：**4b6213d69aa60a4003844457fabba5d05cf6ffdd**。固定阶段标签 **ms-i2h-a1** 包含随后状态记录；本轮atomic推送后按ls-remote核对integration和标签，远程结果以实际命令回执为准。worker开工ms-i2h-start不移动。按本次指示先完成A；以下交付先登记待验收，没有修改其worktree或发送聊天消息。

| Session / 包 | 用户报告源码 / handoff | 状态 |
| --- | --- | --- |
| B / MS-C6 | 467b743873a347f30e1954f74ab1f0246797ae23 / 1cd90da9c3cebb5da551913dbb0cbee5bace9832 | 已报告246单元＋105 SQL；待审阅/合入/接线 |
| C / MS-T2e | 27fe04f22cf19f734f776da326e79dc52eb7b83e / 94c75066ed1c9a2ddb7f48a871ddafa957d5ba2d | 已报告218单元＋124不同SQL；待审阅/合入/接线 |
| D / MS-R2e | ced41378d814b7bfbb641eb531fd875646050776 / 7d6ee06e35de0dfb89bdec6fbdf3de29e54109f9 | 已报告431项与OS清理；待审阅/合入/接线 |

上表计数来自用户转发，当前尚未独立核对worker原始回执，不能写为accepted。各包停在原交付边界；下一包未派发。


日期：2026-10-08。A维护。**MS-I2g实际来源与装配开发集成已接受。B/C/D阶段版已分别合入；C/MS-T2d和D/MS-R2d已按最终组件范围接受，B/MS-C5最终8cc445a/233a5c3已合入b47fd81并按组件接受。完整回归覆盖1077个不同节点，最终接受覆盖均通过：首轮1076通过/1测试超时，定向修复后受影响模块3项通过；去重采用首轮其余1074＋复跑3。原841全部保留，新增236，两个批次实际合计4289.46秒。完整开发集成范围接受；最新完整标签ms-i2g，worker开工标签仍为ms-i2h-start。**


## 最新完整开发集成：ms-i2g

- 实际代码/证据提交：**5d42970d1dd6761f33351c6e54f22e6f7fce312d**，含三个最终组件、A当前来源/内部装配及测试watchdog兼容修复。ms-i2g固定标签包含随后状态元数据；运行源码与213份来源摘要在该提交一致。
- 首轮1077节点：1076通过、1测试超时；原代码单独复跑通过后，仅修复20→60秒测试防挂起时限，受影响模块3项通过。最终去重1074＋3=1077接受覆盖，原841全部保留，新增236。原失败/定向复跑/汇总XML均保留；不是一次1077全通过。
- Ruff、188文件格式、Mypy117源码、1282schemas/272接口/304反例和并行目录/依赖检查通过。正式范围见[MS-I2g](../implementation/MS-I2g.md)。
- B/C/D下一包继续固定 **ms-i2h-start / f5b08fa6dcc653c0cd3939a32f36deeb0e51dff8**，不在包中途同步新验收标签；本次兼容修复在A集成测试文件，worker下次最终合入由A保留。没有修改worker分支或给聊天发消息。
- MS-I2g按开发集成范围accepted；P1产品、真实模型/认证/IPC/用户确认和文件进程执行仍未accepted，flags未变。
## 历史接线阶段：ms-i2g-a1

- 源码/证据提交：**8b581af6eca951a2af2919361feaaeb85afa2477**；固定阶段标签ms-i2g-a1包含随后状态记录，不移动ms-i2g-start或旧集成标签。
- A当前来源/内部装配与C/D最终组件接受完成。234/41/27三个实际批次去重268项通过；Ruff/格式186文件/Mypy117源码通过。详见[实际范围](../implementation/MS-I2g-A1.md)及[方法/输入输出/策略](requests/A/MS-I2g-wiring.md)。
- 该阶段不是完整MS-I2g里程碑，历史全量841仍属于ms-i2f2。B继续固定ms-i2g-start完成MS-C5；C/D本包无需重做，下一包未派发。没有代替worker切分支、合并或发聊天消息。
- 新增RunToolAccessBinding及其文档/资源副本；旧请求/响应、shared ports/contracts、uv.lock不变。当前schema/hash以environment.json和该阶段标签为准。

## 历史完整运行版本（ms-i2f2）

- 目录/分支：`E:/UAW` / `integration`；仓库：[Guozai3633/UAW](https://github.com/Guozai3633/UAW)。
- 已验证代码/证据提交：`9422fcaba180fdc04515c993776e7f4a09d526b2`；固定标签 **ms-i2f2** 包含随后状态记录，旧标签不移动。
- 全量 **841 passed，0 failure/error/skip**；Ruff/格式156文件，Mypy102源码文件通过。1281 schemas、272接口、26已实现公开操作。
- 新增231项检查，原610项完整重跑。[实际范围/回执](../implementation/MS-I2f2.md) 与 [接口/目录/策略](requests/A/MS-I2f2-integration.md)。
- Worker原开工基线是 `ms-i2e / ba2f3b0d9417e6d695eaa74c2f766217c98b01f1`；A原基线是 `ms-i2f1 / d3fca34528237da155617a2a86df2abcb0db86b3`。交付后再同步新版本，不中途换基线。

## 历史MS-I2f2接受

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
| B | MS-C5 | 通用登记/当前authority/Reader→快照→模型输入 | 阶段d0ad58f合入80b86b7；最终8cc445a/233a5c3合入b47fd81；208单元＋85不同SQL按组件接受 |
| C | MS-T2d | 只读调用编排/实际text adapter/持久结果Lookup与Reader | 阶段717c237合入e1503dc；最终859f5d0/db09a69合入5721ad4；162单元＋100不同SQL按组件范围接受 |
| D | MS-R2d | 真实OS控制签名/授权根来源/装配验证 | 阶段1287a05合入0be96be；最终7d946de/366c916合入b735407；326项通过，OS passed/cleaned；按组件范围接受 |
| E | 未派发 | 保持可选 | 不创建新工作区 |

C 的100个SQL是首轮原70＋最终新增30的不同通过节点覆盖，不是一次100项运行；首轮新增测试decline枚举错误已修复并完整复跑新增路径，原失败回执保留。D 的326项是worker实际模块/原共享回归，A不重新接管全模块执行。具体接线见 [MS-I2g当前来源](requests/A/MS-I2g-wiring.md)。完整P1、真实LLM/IPC/用户确认/执行仍未验收，flags未开放。

每包四个连续里程碑、两个交付点；阶段版接口提交后继续同包，不等待最终集成才做后半包。具体输入输出、策略、目录和数据库命令见[发包定义](requests/A/MS-I2g-parallel-packages.md)，可转发内容见[NEXT_WAVE](NEXT_WAVE.md)。A没有替worker切分支或向其聊天发消息。

完整MS-I2f/MS-I2/MS-T2/MS-R2仍未接受，D01/D03/D06不因此改变。B/C/D按accepted_component记录；不把局部组件接受提升为整轮产品接受。

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

## 下一轮准备：ms-i2h-start

[MS-I2h详细范围](requests/A/MS-I2h-parallel-packages.md)：A单Agent根实例/循环，B/MS-C6多规则语义评估与读取测量，C/MS-T2e权限先行混合工具检索，D/MS-R2e实际file.read组件。四个连续里程碑、两个交付点，互不依赖开发分支。固定开发标签ms-i2h-start发布；代码合并来源b47fd81及当前2条组合链（274.16秒）通过，Ruff/188格式/Mypy117通过，worker按NEXT_WAVE同步开新包。完整1077节点随后由A通过，验收标签ms-i2g单独发布；worker仍按ms-i2h-start开发，不移动该标签。实际标签SHA由git rev-parse ms-i2h-start^{commit}核对，实际发布回执见下节。

### ms-i2h-start实际发布回执与固定摘要

- 固定开发标签及远程peeled commit：**f5b08fa6dcc653c0cd3939a32f36deeb0e51dff8**；atomic push已成功，ls-remote实际核对integration和标签一致。标签不移动；后续完整MS-I2g验收标签另发，worker不在包中途换基线。
- B/C/D新包状态published_ready_to_start，实际开工以其报告为准；A没有替其同步或向聊天发消息。历史ms-i2g-start表不用于新包摘要。

| 文件 | ms-i2h-start SHA256 |
| --- | --- |
| `contracts/uaw.schema.json` | `595ebe8f9173b5a6c8608dfac9f339f1c4c7f8e7e5f0599687f04bf6511ef90d` |
| `src/uaw/shared/ports.py` | `fd45911eeb0e72b56459d012c4c6e8130e5d6abfabe77140bf443a8a103ba104` |
| `src/uaw/shared/contracts.py` | `08ac0c164c56c6142f3f4397bcd2c3a544e2abacc3432bf4a10d180fcb5fce7b` |
| `uv.lock` | `a065f5af348ed573e7f2547a62ec393366a499103a6e0c791686a8404b89c59f` |
| `src/uaw/resources/prompts/intent-understand-v1.txt` | `3f91702614fca270d1c8b6e3dd2842a950dbfa01685b58d5aa54cbce36114400` |
