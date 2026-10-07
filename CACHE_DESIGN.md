# UAW 多层缓存与复用设计

状态：v0.2 讨论稿，配套架构 v0.9。本文定义目标机制和实施优先级，不代表缓存已实现或有实测收益。技术栈和模型供应商仍未确定；供应商特有的缓存接口由 Model Runtime 适配。根据 Notion 缓存题集补充的在途等待/取消与发布边界见 [ENGINEERING_COMPLETENESS.md](ENGINEERING_COMPLETENESS.md) §7。

## 1. 目标与模块归属

目标是在权限、输入版本、用户要求的新鲜度和交付质量成立时，降低每个可接受成果的总成本、首响应和完成时间。命中率只是过程指标；不能用增加无关输入、复用过期数据或无限保留上下文来提高数字。

保留七个 Runtime。增加共享基础设施 `CacheManager`，提供 namespace、key 编码、读写、有效性元数据、并发去重、配额淘汰、失效通知和指标接口；每个 Runtime 决定本领域的可缓存性、关键依赖与失效规则，不把语义决策交给缓存服务。缓存透明服务于调用，LLM 不需要每次主动选择“是否开缓存”，也不能调用工具绕过权限/新鲜度限制。

先区分三种复用：

- 供应商提示词缓存：复用模型输入前缀的处理，仍生成当前请求的输出。
- 应用结果缓存：复用已经得到的解析、检索或只读工具结果，可能省掉一次调用。
- 在途请求合并：相同且允许共享的并发读取，只计算一次，再让等待者各自校验后取结果。

历史日志、Run 状态、幂等账本、审批和唯一的产物副本是权威记录，不是可随意淘汰的缓存。缓存丢失应能从这些记录或原始输入重建。

## 2. 两个维度：缓存什么与存在哪里

### 2.1 按业务内容划分

| 缓存对象 | 所属模块 | key 的关键依赖 | 新鲜度/失效依据 | 首版建议 |
| --- | --- | --- | --- | --- |
| 草稿与历史显示 | Interaction / Run | user、conversation、Item revision、cursor | 服务端新事件、退出账号、删除 | 缓存近期显示，Run 状态回权威源 |
| Skill/Role/工具 schema | Agent / Tool / Context | 包/定义/schema 版本、内容 hash | 更新、撤销、flag/权限变化 | 高优先级，稳定装配 |
| 模型目录及能力元数据 | Model | provider、用户可见域、catalog revision | 模型状态/账号/政策变化 | 可缓存元数据，调用仍核验政策 |
| 文件解析、切片和 embedding | Context / Knowledge | 原始内容 hash、解析/切片/embedding 版本与设置 | 文件版本或处理算法变化 | 高优先级，可按块增量 |
| 工具发现候选 | Tool | 查询、可见范围、registry/index/排名版本 | 工具更新、索引更新、权限/flag变化 | 精确复用检索，不缓存授权结论 |
| 材料召回结果 | Context | 查询、corpus/index revision、ACL、过滤/排名参数 | 材料/记忆更新或删除、检索政策变化 | 缓存引用与版本，使用前验证 |
| 摘要、压缩块、证据片段 | Context | 输入集合/版本、prompt/model/参数、purpose | 任一来源或方法/政策变化 | 相同输入与目的可复用 |
| Prompt 前缀 | Context / Model | 实际模型、指令/工具/schema/角色/技能版本、序列化设置 | 前缀或兼容设置变化、供应商保留期 | 稳定序列，实际命中由供应商报告 |
| 只读工具输出 | Tool | tool/provider 版本、参数、账号资源、source revision/freshness | 数据变化或新鲜度边界 | 按工具登记，默认不泛化所有读取 |
| 计算/构建/检查中间产物 | Workspace / Tool | 输入文件、环境/依赖、代码/参数、种子/模式 | 依赖改变、校验版本改变 | 确定且隔离的任务可复用 |
| 最终答案/计划/执行建议 | Agent / Intent | 完整任务与依赖、角色/模型/规则/用户约束 | 任一有效输入变化 | 自由任务默认不直接复用；受控任务另设契约 |

表中版本是依赖声明：每种对象只纳入实际影响结果的版本，不能粗暴把全系统 revision 放进所有 key，也不能漏掉真实依赖。

### 2.2 按存储位置划分

1. 浏览器缓存：只承担草稿/展示和已授权近期数据，不作为执行/审批权威。
2. Run/进程内缓存：热点 schema、反复读取的片段、已固定 Context Block 和在途读取合并。
3. 共享服务端缓存（需要多 worker 时启用）：跨进程共享同权限域的可复用结果。
4. 持久派生存储：文件解析、embedding、验证产物等高成本可重建数据，通过原始对象与版本引用复用。
5. 供应商模型缓存：外部推理服务管理的前缀状态，UAW 记录使用与配置，不假设直接控制 KV 内部状态。

业务缓存种类与这些存储层可组合。第一阶段可先用进程内存和现有存储适配器，不要求为设计立即增加独立分布式服务。共享 store 的引入由重复计算和多 worker 的证据决定。

## 3. CacheManager 与 key 契约

概念接口：`get / put / get_or_compute / invalidate_dependency / record_usage`。业务模块先提供有效性要求和 scope，再用缓存；命中后的资源归属/当前权限复核仍归业务模块。

`CacheRequest`：kind、scope、source_refs/revisions、规范化参数、实现/prompt/model/schema 版本、freshness_policy、reuse_policy、有效权限范围、缓存预算。

`CacheEntry`：key、value_ref、dependency_refs/revisions、access_scope、created_at、source_observed_at、expires_at、freshness/status、producer_version、数据保留政策、size、origin/evidence_refs。`CacheOutcome` 返回 hit/miss/revalidated/coalesced/bypassed，附验证后的引用与新鲜度状态。

```text
key = namespace + cache_kind + hash(canonical_relevant_inputs)

canonical_relevant_inputs 包含：
  真正影响语义的参数、来源与版本、账号/访问域、处理配置及版本、要求的新鲜度。
```

对象字段可稳定序列化；保持有语义的数组/消息/步骤顺序，不为了 key 一致排序整段对话。参数规范化仅做工具明确允许的变换；“相同 URL”不能忽略账号、语言、请求 header 或资源版本等实际差异。哈希不等于匿名化，私人内容仍需要私有 namespace 和保留政策。

request_id、trace_id、生成时间、进度秒数等纯追踪字段不进入纯计算缓存的 key；真实日期、用户时区、用户指定模型、分支内容和数据范围如果影响结果则必须进入。不能为了复用移除“截至今天”等语义条件。

优先使用不可变内容/块 hash、局部资源 revision 和显式依赖；查询型结果再加 corpus/index revision、ACL/filter hash 和 freshness window。用户明确模型 A 时，与 B 产出的模型派生结果不能冒充 A 的本次结果；缓存 key 和 provenance 保留实际生产模型。Auto 的具体选择也记录 resolved model。

## 4. 提示词缓存：保持真实模型输入稳定

### 4.1 Context Block 与逻辑布局

Context Runtime 把内容装成有版本的 `ContextBlock`：block_id、内容 hash、scope、kind、source refs、renderer_version 和依赖。逻辑布局建议：

```text
稳定的公共核心 / 基础工具
  → 角色与已固定工具/技能（在当前执行阶段内稳定）
  → 已确认任务与固定来源快照
  → 当前 Agent 的已装配历史与结果
  → 当前请求的动态状态/新消息
```

这只是逻辑顺序；供应商可能将 tools/output schema 等放在模型实际序列的其他位置。Model Runtime 的 `PromptCacheAdapter` 按实际 provider/model 能力装配并验证 fingerprint，不假设拼接字符串的位置就是最终 cache breakpoint。

共同核心可提高同模型同授权域请求的前缀复用机会，但不同角色/工具集会在分歧处结束共用前缀。父子 Agent 不复制全部历史来追求命中；它们可复用允许访问的原始材料块、解析结果与摘要，仍按自己的目标构建上下文。

### 4.2 稳定性规则

1. 核心指令、角色定义、技能和 schema 版本固定；按确定顺序渲染，不每轮重新措辞或随机调整顺序。
2. 动态时间、剩余预算、进度和 trace 信息放在适用的后部状态块；安全政策的当前版本仍在正确的可信指令层，不能为命中移成普通数据。
3. 对有效历史和工具结果尽量追加，不无故改写已经装配的内容；用户纠正可追加明确修订。删除/撤销、过期证据或权限变化需立即停止装配受影响内容，即使损失命中。
4. 工具按需发现后，在当前阶段内稳定其 schema/ID/顺序。切换阶段时可以变更，不为命中保留无关的大目录。
5. 检索排序确定：同分引用有稳定 tie-break，片段格式/引用方式固定。不固定过期结果或漏掉更相关新材料。
6. 模型、格式/工具配置等按用户政策和实际需求控制；缓存只能在兼容调用条件下争取复用，不能自行换模型。

工具动态加载由 provider adapter 处理：支持延迟发现/追加工具描述时用兼容机制；仅支持全量 tools 请求时，保留小型基础集和阶段内稳定工具集，接受扩展边界的 miss。定义与可调用权限分开，撤销权限立即阻止执行，不为缓存沿用旧许可。

### 4.3 历史增长与压缩

节点可以每次重建临时 Context Snapshot，同时引用相同 ContextBlock；临时上下文不意味着重写所有文本。Agent 自己的局部循环可保持已用的有效序列，兄弟 Agent 仍隔离。

逻辑数据流的“只传引用”与模型 API 的输入不同：共享存储引用能减少重复读取/处理，但模型不天然认识一个内部 artifact_id，也不会因引用已缓存就自动读取其内容。Adapter 必须把必要片段实际装入输入，或使用 provider 明确支持且已授权的内容/会话引用机制；应用层命中不能伪装成省掉了模型输入 Token。

达到上下文/成本预算或出现明显低相关历史时进行有版本压缩：固定核心 → 可复用的分段摘要 → 近期未压缩窗口 → 当前输入。摘要按 episode/已完成阶段增量形成，不每个 Token 或每一步重生成全部摘要。压缩切换形成新 context_epoch，记录旧/新依赖；其后请求在新布局内复用。

一次压缩可能损失之前的模型前缀命中，但减少后续输入。比较“继续累积的总成本”与“压缩生成成本 + 新输入/写入成本 + 后续读取成本”，包括输出、上下文质量和时延；不以单次缓存命中率阻止必要压缩。

### 4.4 Provider 适配与预热

`PromptCacheCapabilities` 声明实际 provider/model 是否支持缓存、最小资格条件、隐式/显式断点、保留/路由配置、工具追加机制、usage 字段和计费维度。参数和费率从已选模型的当前官方资料/供应商配置取得，不在核心写死单一模型行为。不支持时正常调用，usage 的缺失不能当 0 成本或 0 miss。

预热只在能力支持、复用概率高、数据保留允许且预算划算时使用，先计算调用/写入成本；不为了达到门槛插入无关文字，也不对私人项目做无授权跨用户预热。应用 fingerprint 一致只说明具备复用条件，实际命中仍由供应商报告，不能承诺 100%。

## 5. 解析、embedding、检索与工具发现

### 5.1 处理结果按内容复用

文件上传按获准范围生成内容 hash。相同文件重新上传或多个 Agent 阅读时，可以复用解析/切片/embedding 产物；原始 Asset ID 和引用归属独立，不因为相同 hash 就泄露别人是否上传过材料。

文件只改一部分时，依据结构与 chunk hash 复用未变化块，并重建受影响索引/定位引用。解析器、OCR、切片参数或 embedding 模型变化时，对应派生产物另开版本。摘要还包括 prompt/model/生成配置，来源、目的不同不能强行共享。

### 5.2 检索缓存的两阶段

先查缓存的候选引用/版本 → 核对当前权限、来源可用性与要求新鲜度 → 加载有效内容与确定性排序 → Context Runtime 装配。工具发现同理，使用前查权威 Tool Registry，不把昨天的“可用工具”当今天的许可。

跨不同 corpus、记忆读写政策、ACL 或索引版本不能只按 query 文本复用；embedding 相似用于召回候选，不证明两次任务/查询等价。权限过滤先于候选暴露，缓存结果也不能把无权读取资源的标题和存在性泄露给用户。

## 6. Tool Runtime 中的结果缓存

ToolSpec 增加 `cache_policy`：mode（disabled/content_version/ttl/revalidate）、safe_to_reuse、key_fields、dependency_resolver、freshness_rule、可复用失败类型、共享范围、最大对象/保留、缓存输出语义。所有工具缺省为 disabled，明确登记后才复用。

只读不自动等于可缓存：当前余额、账号权限、任务状态或明确要求最新的网页读取可能需要实时验证。工具输出保留原 source_observed_at / fetched_at 与 version；cached served_at 不冒充重新获取时间。当前用户/任务需要的证据来源必须保留。

缓存命中仍返回一次当前调用对应的 ToolResult/Item，标记 from_cache 和 origin_ref，维持审计与引用链。产物旧引用需检查仍存在且可访问；必要时复制/物化到当前隔离工作区。

| 工具性质 | 推荐策略 |
| --- | --- |
| 读取明确不可变版本的材料 | 内容/版本 key，可长期复用，仍复核权限 |
| 本地文件读取 | 分支快照/文件内容 hash；用户编辑立刻产生新 key |
| 普通网页/搜索 | 工具规定 TTL 或条件重验证；新鲜度强请求绕过过期结果 |
| 纯计算/隔离确定性检查 | 全部代码/数据/依赖与参数版本匹配才复用 |
| 发送/发布/创建子 Agent/撤销/委派启动 | 不做结果缓存；使用权威幂等账本与状态查询 |
| 权限或审批决定 | 当前执行校验，不复用旧批准冒充新批准 |

负缓存仅对明确、稳定且不会泄露资源存在性的失败短时适用，例如工具登记的版本不存在；瞬时网络失败/限流、解析模型失败不长时间缓存。账号权限错误需跟授权状态变化失效，不把拒绝固定到长期缓存。

## 7. 并发去重、击穿与竞争

相同 scope/key 且可共享读取的两个 Agent 使用 single-flight/get_or_compute：第一个执行，其他等待有限时间；成功后每个等待者检查各自权限与有效版本，再接收结果。一个等待者取消不会取消仍被其他请求需要的计算。

单进程先用在途任务表；多 worker 再考虑带租约和 fencing token 的共享锁。生产者完成后先核对依赖 revision，再发布结果；计算中源文件已改变，旧结果只能绑定旧的明确快照，不能标成最新。写入使用 CAS 防止过期生产者覆盖新结果。

TTL 可有受 freshness 上限约束的抖动，热点可提前刷新，但不能超出用户指定的新鲜度。超时/竞争时允许安全只读重新计算；副作用调用去重归幂等协议，不能用缓存锁保证外部 exactly-once。错误 stale 数据是否可展示由业务策略明确决定，实时任务默认不采用 stale-while-revalidate。

## 8. 失效、撤销与权限

每个 entry 存 dependency_tags。事件包括 file.changed、workspace.merged、asset.deleted、memory.updated/deleted、skill/agent/tool/rule.updated、feature_flag.changed、auth.revoked、model_policy.changed、索引 revision 变化。

不可变版本 key 让新请求自然 miss；依赖索引用于删除或禁止旧引用再次访问。权限撤销/用户删除还需权威 tombstone/权限检查，不能只依靠异步删除缓存。当前调用在使用/返回前核对相关版本；不能依赖“缓存还存在”证明仍有权使用。

来源删除或记忆撤销时，相关摘要、embedding、检索、ContextBlock 与应用结果缓存失效。原始权威历史的保留/删除按数据政策执行；已经向外部模型发送的内容或供应商保存的缓存不能靠本地删除声称立刻抹除，需要 provider 能力与保留政策单独管理。

私人内容 namespace 至少区分 user 和授权资源域；公开通用规则/工具说明可共享，私人文件、用户记忆、账号工具结果只在获准域内共享。不包含凭据/token 的缓存 key、prompt、日志和向量文本；敏感参数使用受控引用，存储遵守保留和访问限制。不要把本地 hash 日志当无敏感信息。

## 9. 答案、计划和语义缓存的边界

默认不按“问题向量很相似”直接返回另一任务的答案/计划。时间、材料、数字、用户约束、模型政策、已执行副作用或前提差异都可能改变结果。可把相似成功任务召回为 Skill/TaskTemplate/参考结果，经当前 LLM 和约束核对后使用。

受控确定性任务或用户认可的固定问答模板可单独声明 exact-result reuse_policy：完整输入、来源/角色/规则/模型/格式版本相同，且新鲜度/授权/质量要求满足才直接复用；声明结果复用语义，不冒充重新生成。工具调用、用户审批和新任务状态变化不得由旧模型输出自动执行。

执行评估和计划默认按当前输入/资源复评；已接受的计划快照可作为当前任务继续执行的状态，不是按近似问题套用的缓存。缓存评估建议也必须重新校验资源、预算与用户新要求。

## 10. 成本、命中与质量观测

按 cache_kind、role、provider/model、任务类别统计：eligible requests、hit/miss/bypassed/revalidated/coalesced、数据年龄、耗时、失效原因、对象大小、错误复用、内存/存储成本和独立调用节省。命中分母只算可缓存请求，并同步给出不可缓存占比，避免高数字误导。

模型层记录 input/cached-input/cache-write（若 provider 提供）/output/工具与环境费用、首 Token 时延和完整 Run 时延。展示有效缓存 Token 比率及真实账单成本；不能仅以命中请求数判断长短前缀收益。没有 cache-write 报告时注明无法准确分解，而不将其假定为免费。

理论比较形式：

```text
无缓存成本 ≈ N × 输入处理成本 + 输出及其他成本
缓存方案成本 ≈ 缓存写入/刷新 + 后续读取 + 未命中处理
             + 缓存系统开销 + 输出及其他成本
```

实际计价由 provider 决定；UAW 以所有尝试、失败、重试和缓存维护的总成本除以可接受成果数。和未启用缓存的同版本任务对照，检查成果质量、引用、删除/撤销、当前授权和用户时效要求。

命中损失定位：prompt/schema 版本变化、工具集合顺序变化、动态字段位置、历史压缩、source/corpus 变化、模型变化、过期/撤销、权限不同、供应商路由/保留等。先修真实浪费，不能用降低质量或延后权限撤销来换命中。

## 11. 首版实施顺序与未定参数

1. 先记录成本/时延与 fingerprint，加入稳定核心/工具序列化、版本化 ContextBlock 和透明 provenance；不预估不存在的收益。
2. 实现内容版本的解析/embedding/片段复用、schema/技能热点缓存和单进程只读 single-flight。
3. 接入所选 provider 的 PromptCacheAdapter、阶段内工具集和压缩策略；按账单、输入量和质量调优。
4. 为明确有收益的只读工具登记 TTL/revalidate，加入 query/corpus/权限版本的检索缓存；验证删除/失效。
5. 有多个 worker 和跨 Run 重复计算时才增加共享缓存和租约锁。自由语义答案缓存与广泛预热后置。

TTL、容量、淘汰频率、摘要触发阈值、候选数和允许陈旧窗口需要根据具体工具/provider/真实任务决定，不现在写死。先用按 scope 配额、大小/成本约束的淘汰；昂贵可复用派生产物与廉价短期热点区分保留，防止一个项目挤占全部缓存。

首批验收：同文件多 Agent 阅读只解析一次；文件改动/记忆删除/工具撤销后不返回过期授权数据；前缀稳定的调用能观察实际 provider 命中；压缩后整体成本仍合理；外部写动作不被结果缓存略过或重复；缓存不可用时按正常路径工作且副作用状态仍可靠。

### 11.1 同一论文的复用示例

用户上传论文 V1 → 解析/切片/embedding 各以内容与处理版本登记 → 阅读 Agent 与审查 Agent 同时请求时合并获准的相同计算 → 各自引用获准片段并构建独立上下文 → Model Runtime 在实际前缀可匹配时获取 provider 缓存收益。

用户再问同一论文的新问题，可命中文件处理结果，新的检索 query 和回答仍按任务执行。论文变 V2 时仅复用不变块，并更新页码/引用映射；V1 只能在明确要求旧版本且仍有权访问时使用。用户撤回材料或记忆许可时相关缓存不可继续返回。此例分别体现解析复用、在途合并、块复用和模型缓存，不能把其中一种命中等同于全部层都命中。

## 12. 官方资料与 UAW 自有设计的边界

代码验证缓存的补充约束见 [DELIVERY_VERIFICATION.md](DELIVERY_VERIFICATION.md)：报告记录实际受测版本、环境和缓存来源；依赖变化需核验/重验，要求新执行的检查不直接复用旧测试。管理员服务/政策版本参与相关缓存失效，见 [ADMIN_CONFIGURATION.md](ADMIN_CONFIGURATION.md)。

OpenAI 官方说明提示词缓存依赖可匹配的前缀与兼容请求设置；工具定义、顺序和历史改写会影响复用。工具搜索的延迟加载可保留已有前缀。本文据此提出稳定 ContextBlock/阶段工具集；不同模型的阈值、保留、计费和配置由适配器再核对，不把一种接口套到所有 provider。

- [Prompt caching](https://developers.openai.com/api/docs/guides/prompt-caching)
- [Prompt cache diagnostics](https://developers.openai.com/api/docs/guides/prompt-caching/diagnostics)
- [Tool search](https://developers.openai.com/api/docs/guides/tools-tool-search)

CacheManager、依赖 key、失效、私有 namespace 和业务复用策略是 UAW 的拟定架构，尚未验证容量或成本收益。
