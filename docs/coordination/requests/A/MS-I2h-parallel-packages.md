# MS-I2h：进入单 Agent 循环的并行能力包

日期：2026-10-08。A维护。开工版本使用固定标签 **ms-i2h-start**，实际 SHA、发布状态以 [DISPATCH](../../DISPATCH.md) 为准；该开发基线包含三个已接受组件及当前两条装配复验；MS-I2g全量由A继续，不作为worker独立开发的等待条件。旧 MS-C5/MS-T2d/MS-R2d 已交付，不重复派发。

## 1. 目标与边界

本轮使主 Agent 能使用已经接好的 Context、Model、Tool；并补充多规则上下文、可扩展工具检索和真实只读文件适配器。四个 session 使用同一个已提交基线，各自只依赖该基线，不读取其他 worker 开发分支。

| Session | 包 | 能力范围 | 本轮不依赖其他 worker 的部分 |
| --- | --- | --- | --- |
| A | MS-I2h | 根实例、有限步单 Agent 循环、当前来源与阶段版装配 | 已发布的 Context/Model/纯文本 Tool 入口 |
| B | MS-C6 | 多规则语义评估接入、当前版本复查、读取成本测量 | 已发布 RulePlan/Reader/Run/固定模型窗口；评估器为显式内部 port |
| C | MS-T2e | 权限先行的混合检索、向量索引缓存、检索扩展入口 | 当前 ToolRegistry/ToolAccess；embedding 为显式内部 port |
| D | MS-R2e | 已签名 file.read 的真实有界读取、来源核验、终态 journal | 当前准入/根来源/签名/独立主体映射；仅临时测试根 |

每包四个连续里程碑。完成前两项提交固定接口、调用样例、修改目录和 SHA，然后继续后两项，A同时接线。公共 schema/ports、迁移、依赖锁、Run/Model/API、组装根与全局事件归 A；缺口先提交精确提案，不私加公共字段。没有真实提供方的分支明确不可用。

本轮仍是独立组件开发，不把 P1-07/08、完整配对或产品可用性提前标 accepted。默认 flags 和公开 Runtime 绑定不因发包开启。D03 尚未决定的 exec/写入/安装继续不具备执行入口；D06 真实模型/embedding 提供方由管理员配置。纯文本任务的 Agent 组件可以先实现，不强制等待本机执行功能。

## 2. B / MS-C6：多规则与有界读取

### 目录及接口

允许原 B 路径：`src/uaw/context/`（排除 A 的 seed.py/intent.py）、`tests/unit/context/`、`tests/integration/context/`、B requests/handoff。建议新增 `assessment.py`，修改 readers/rules/ports 及相关测试。不能导入 Model 私有 ProviderRequest 或直接更改模型配置。

阶段版给出：

```python
class RegisteredRuleAssessor(Protocol):
    async def assess(self, candidates: tuple[RuleCandidate, ...],
                     ctx: TrustedExecutionContext) -> RulePlan: ...

RegisteredRuleProvider(inputs, *, assessor: RegisteredRuleAssessor | None = None)
```

旧构造保持有效；空/单规则沿用现有行为，多规则缺 assessor 明确 unavailable。A负责从固定模型接口实现评估 adapter；B可用受控评估器检查协议，不能声称已验证模型语义质量。port 输出必须在 Context 边界重新验证。

### 四个里程碑

1. 读取实际登记且固定版本的规则，形成有界候选集合。复制传给 assessor 的对象，实际 rule 正文/level/scope/source_ref 不可由模型变更；不得添加未登记规则或扩大来源。支持原 RulePlan 的 topic/value/critical/supersedes/conflict_refs，但不能伪造高优先级来源。
2. 接多规则评估与现有优先级解析。评估不完整、结果格式错误、缺失候选、伪造或重复 Ref、越权覆盖、重要冲突分别明确失败或要求澄清。冲突来自语义 port，不能用词典代替；冲突 Ref 必须属于实际固定候选。模型建议不能撤销 Runtime 权限规则。模型等待前后复查配方、材料、规则、工具、Run/权限/固定模型和期限。
3. 走登记→build→固定 snapshot→ModelPrompt/引用链，测量各边界 RecordStore.get/Reader/assessor 次数及耗时，比较相同输入和拒绝行为。落实 [读取反馈](MS-C5-read-amplification.md) 中仍存在的重复展开；允许优化一次操作内的已读内容和批量策略，不允许跨请求缓存授权、撤销或取消状态。若需公共批读 port，先提案，不改 shared/存储实现。
4. 在 B 的 55433 实跑多规则、修订/撤销、模型等待期间变化、并发/重启、缓存开关与原 Context SQL/单元。提交不同节点回执索引，保留失败和定向修复历史。性能报告给出实测条件与查询数，不伪称生产延迟达标。

验收看实际规则溯源、拒绝行为和模型输入一致性。不得通过删检查提高性能；不能把材料指令提升成规则，也不能把评估的布尔值当授权。

## 3. C / MS-T2e：工具发现扩展

### 目录及接口

允许原 C 路径：`src/uaw/tool/`、C unit/integration、requests/handoff。建议新增 `retrieval.py`、`index.py`，保留现有小目录 discover 默认兼容。阶段版固定异步 `ToolRetriever.discover(query, categories, max_candidates, ctx)` 和可选 facade 注入接口，返回已有 DiscoveryResult。

embedding provider 和向量索引是内部显式 ports；固定模型策略仍由 A管理。索引 metadata 至少绑定 ToolSpec 的完整 Ref/hash、embedding 提供方/模型版本、维度和文本规范版本。缓存路径由可信组装传入，不能由模型给出。可以使用标准库 SQLite 保存结构化索引缓存；它不是 ToolSpec 注册权威，也不是权限数据或普通业务状态库。

### 四个里程碑

1. 从实际 ToolRegistry 固定快照产生候选投影，在检索前按当前 role/category、权限、flags、环境和提供方过滤。固定 registry_revision。索引中存在的工具不代表已安装或获权；工具描述是资料，不是系统指令。
2. 实现有界词法召回＋向量召回和确定的融合排序；模型最终选择 Tool。向量必须来自显式 embedding port，检查有限数值/维度/提供方和内容摘要，不得用 hash/random 向量冒充语义。测试可提供已知数值向量验证计算，明确不证明实际 embedding 质量。
3. 实现有界持久索引缓存、原子更新、重启读取、失效与删除；重建以当前 registry 为准。提供显式 lexical-only 模式；semantic-required 缺提供方直接 unavailable，降级需构造配置明确允许，不能静默声称语义召回。默认不自动添加模型或网络 API。索引不能保存用户正文、凭据、授权结果或 Tool 调用结果。
4. 当前来源在 embedding/索引 await 后及返回前再次复查。测试修订/卸载、提供方和 role/flags 变化、取消/期限、跨用户候选泄漏、损坏缓存、重启/并发和稳定排序；C 的 55434 实跑受影响 Tool SQL 和原调用/结果回归。非空 ModelToolSet 验证继续走 A 的当前适配器。

有界建议：沿用 registry 128 工具上限；query 最多8192 UTF-8 bytes、维度最多4096、索引总量最多16MiB，可配置为更小；不得超过现有 CandidateLimit。扩展不执行工具、不绕过审批/预算/资源闸门。共享 feature flag 或持久 schema 需要 A批准并发布版本后使用。

## 4. D / MS-R2e：真实 file.read 组件

### 目录及接口

允许原 D 路径：`apps/local_runner/uaw_runner/`、D拥有的 workspace binding/contracts/ports/repository、D unit/integration、requests/handoff。建议新增 `read_executor.py`。只实现已有 RunnerParametersFile.read / ToolFileReadInput → FileContent；没有公开的 list 契约，不自创目录浏览或 IPC wire。

阶段版给出 `ReadOnlyRunner.execute(command, *, authenticated_principal) -> RunnerReceipt` 构造/签名、依赖 port 和例子。组合现有 AsyncAdmission、RootBindings、独立 owner/channel adapter、设备签名和 LocalReceiptJournal；authenticated_principal 必须来自可信入口，不从 command/body 取出充当独立身份。缺真正 channel/owner/签名/当前 authority 时不可用，测试使用明确受控 adapter。

### 四个里程碑

1. 准入后的固定 file.read 参数进入真实临时根读取。仅 UTF-8 常规文件，总文件最多1MiB，返回片段最多64KiB；超限/二进制/不支持 cursor、location 明确拒绝。whole/text_span 支持范围和字符索引与现有 schema 一致；小文件计算整个文件实际 SHA256，不能把片段摘要声称整个文件摘要。
2. 原子打开后的 OS 文件身份、最终路径和根身份复核，不能仅 resolve 后普通 open 就宣称避免竞争。Windows junction/重解析点、链接替换、根替换、设备/特殊文件、ADS、绝对/越界路径、同时编辑必须明确处理。无法证明句柄仍属于获准根时失败。阻塞 OS 操作移到线程；期限/取消/权限在读取前、关键 await 后、结果提交前检查。不得执行任意 shell 或扫描真实用户根。
3. 构造真实 FileContent，按设备签名写已有终态 journal；原命令/原尝试/完整 owner/根版本、文件 hash 与读取范围一致，payload 不泄露本机绝对路径。重复请求走已有持久一次使用/回执恢复语义，不能重新执行未知发送。恢复读取与新准入分开，当前数据访问不由历史成功回执自行授权。Runner ok 仍不是 Tool业务完成，A 后续提供独立结果核验和引用登记。
4. 实跑临时文件、Unicode/空文件、边界片段、打开期间替换/编辑、撤销/过期/取消、并发一次使用、journal 重启和原 D回归。真实 OS 签名使用随机 fixture namespace 并清理。不得写/安装/exec、改真实用户文件、弹出生产确认或将受控 channel 叫作可信 IPC 实连。

D03 后续决定原生或隔离 exec；这个读组件不作该决定。文件读取当前能力即使在测试可用，产品 file_access 默认仍关闭；A接完整来源和真实授权后再决定开放。

## 5. A / MS-I2h：单 Agent 组件与阶段版接线

- 新 `src/uaw/agent/`、`tests/unit/agent/`、`tests/integration/agent/` 归 A，与 worker 目录无重叠。
- 根 Factory 绑定当前实际 Run、TaskFrame、固定用户模型、RoleProfile、预算和权限；没有子Agent配置时所有模型继承该固定模型，不自动改选候选模型。先实现根实例，不默认创建子树/DAG。
- 按已设计的 AgentEnginePort 和已有 AgentStepRequest/公共决策对象实现内部 port，接有限步 Context→Model→建议校验→Tool→观察循环；LangGraph 在内部封装，业务状态/权限不交给框架自行决定。直接回答与动态工具选择由模型决定，不固定业务流水线。
- waiting/审批/取消/期限、恢复和次数上限可停止；LLM不得直接把 Run 写成 completed。完成提案必须有实际来源与交付物核验，暂未实现的专业核验或外部数据 Reader 不能返回成功。先接实际纯文本链，不把文件/exec 作为所有 Agent 任务的前置。
- 与真实认证/Model配置接线分开标证据；受控协议测试不能宣称真实 LLM任务已完成。公开 Agent路由和 flags 保持当前状态，实际提供方与产品任务验收后再开放。
- B/C/D 阶段版到达即审阅固定签名和公共提案，逐包接受；A只做受影响和跨模块链，全量留集成里程碑，不再次接管 worker 全部 SQL。

## 6. 同步、数据库与交接

三个 worker 继续原目录/分支，工作区干净后 fetch tags、`git merge --ff-only ms-i2h-start`，核对 HEAD 与固定 tag commit一致，`uv sync --frozen`。失败报告，不 reset/rebase，不在同包中途换基线。

每个 worker 在自己进程 dot-source `ops/start-dev-db.ps1 -Session B|C|D`，再按锁运行 Alembic；端口55433/55434/55435，Docker project/volume 独立。URL/密码只写自身 ignored 私有配置，不打印、不复制 A 配置。D不涉及 SQL 的本机检查可不启动数据库。

阶段版/最终源码与 handoff 分开提交，保持工作区干净。报告固定入口/输入输出/失败和取消语义、目录/哈希、实际用例去重、历史失败修复、A接线要求和剩余依赖。本包结束后不自动扩包；A在统一派发表接受。旧包/旧回执/旧标签保持可追溯。
