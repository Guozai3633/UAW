# UAW 执行决策、会话 Agent、模型与历史记录

状态：配套 v0.8 的详细讨论稿。用户明确要求的部分：工具创建会话子 Agent、用户模型继承、查看与撤销变更、首版授权本地项目访问与测试、平台服务由管理员配置。本文对执行决策与历史权威存储给出建议，部署选型仍待讨论。控制工具见 [CONTROL_TOOLS.md](CONTROL_TOOLS.md)，完成校验与引用见 [DELIVERY_VERIFICATION.md](DELIVERY_VERIFICATION.md)，本地与审批见 [LOCAL_APPROVAL_SEMANTIC.md](LOCAL_APPROVAL_SEMANTIC.md)。

## 1. 执行方式由哪些决策组成

父子 Agent 是一种多 Agent 组织关系。首版建议保留一个根 Agent 负责用户目标、预算与汇总，需要时委派子 Agent，不先增加无主协调的群体。

三个决策相互独立：

| 决策 | 选择 | 含义 |
| --- | --- | --- |
| Planning | none / steps / dag | 直接执行、跟踪步骤、显式依赖图 |
| Delegation | single / parent_child | 根 Agent 自己完成，或委派独立子任务 |
| Parallelism | serial / parallel | 顺序执行，或让无依赖/无写冲突的工作同时执行 |

常见组合：简单解释直接由单 Agent 完成；修改一个紧耦合模块可单 Agent 按步骤执行；独立比较几组材料可父子 Agent 并行，再由根 Agent 合并；只有一次批量只读查询时可并发工具调用，无需创建多个 Agent。复杂度高也可能不适合并行，步骤多也不必多人执行。

### 1.1 语义判断入口

`AgentRuntime.assess_execution` 使用用户原文、TaskFrame、少量相关上下文、资源状态、会话子 Agent 目录、用户执行偏好和预算。任务语义由 LLM 判断，代码负责权限、预算、依赖和冲突校验。无需新增长期常驻的“复杂度判断 Agent”：可将理解与执行建议合并在一次结构化 LLM 调用中，再由 Intent Runtime 与 Agent Runtime 分别消费相应字段。复杂或信息不全时，再做有预算的只读探查和复评。

第一次调用可以输出 `answer_or_next_action` 和 `ExecutionAssessment`，避免简单问题先分类、再调用一次模型答复。专门的判断模型也可作为后续 Auto 优化，但用户选了具体模型时不能因此使用另一个模型。

建议的对象示意：

```yaml
execution_assessment:
  input_revision: turn-revision
  planning_level: steps
  delegation: single
  parallelism: serial
  task_features:
    dependencies: tightly_coupled
    scope: one_component
    information_gaps: [unknown_api_contract]
    write_conflicts: possible
  justification: [changes_share_the_same_api_contract]
  evidence_refs: [user_input_ref, workspace_manifest_ref]
  alternatives: [delegate_independent_review_after_edit]
  confidence_band: provisional
  probe_next: inspect_existing_api
  reassess_when: [scope_expands, probe_disagrees, repeated_failure]
  budget_request: bounded_run_budget
```

该 schema 仅表示设计，不是预先写死的业务分类。无需一个 1~10 总分决定一切；置信度只表示有待证据检验的判断，不能视为模型已校准概率。模型输出结构损坏时先有限修复，同一模型依然失败则向用户报告，不能因解析失败默认最高成本执行。

首次评估必须提供稳定的身份/职责/决策原则与动态资源目录，不能期待模型自行知道 UAW 的执行能力。可审阅模板见 [任务理解与执行决策提示词](prompts/execution_assessment.md)，字段级输出约束见 [ExecutionAssessment JSON Schema](contracts/execution_assessment.schema.json)。上面的 YAML 是概念示意；JSON Schema v0.1 是新增的字段草案，后续实现以版本化契约为准。首次调用可输出 understanding、execution 和 next_action；若选规划，再调用独立 Planner 模板生成步骤或图。

### 1.2 决策依据与执行链路

LLM 判断目标是否明确、交付物与步骤、依赖是否紧耦合、能否独立验收子成果、是否存在跨专业任务、上下文量、资源写冲突、预估增量成本和合并负担。资料不够时先确定缺口；用户明确要求单 Agent、多 Agent 或先计划时遵循该偏好，并解释权限/资源造成的限制。

```text
模型继承政策解析
  → 原文与最小上下文
  → LLM 提出理解、执行建议或直接答案
  → Agent Runtime 校验用户偏好、预算、已知资源条件
  → 直接循环 / 单 Agent 步骤计划 / 委派与依赖图
  → 工具与子任务结果
  → 发现新条件时局部复评
  → 验证并交付
```

不确定时建议先用单 Agent 加简短计划/只读探查，保留升级能力。高风险但语义不明确的动作先澄清；增加 Agent 数不能解决缺失的用户意图。

用户可选择 `Auto`、`单 Agent`、`协作优先`、`先规划` 等执行偏好，并可用自然语言表达。执行偏好与模型选择是不同设置。所谓“最高规格”建议定义为更充分的规划、证据和审查预算，在已有权限与模型选择内执行；仍有总预算和并发上限，不强制所有节点并行或递归委派。成本与耗时增加后是否提高质量需要真实任务比较。

## 2. Planning、DAG 与并发

Planning 用于明确目标、步骤、完成条件和风险。`steps` 是有版本的步骤清单，可由同一个 Agent 顺序执行；不需要为每个步骤再造子 Agent。

`dag` 在需要调度独立成果时使用。Planner 先生成真实依赖，Scheduler 再找可执行节点，不能为了并行把依赖删掉。节点执行形式可为函数、工具、LLM 调用、Agent 循环或子 Agent。父子关系表达委派管理，DAG 边表达输入依赖；兄弟 Agent 可以并发，也可以等待依赖。

RAG 用于检索材料并构建上下文，不是这张执行图。执行图中的调研节点可以使用 RAG，但启动 RAG 不自动要求 Planner 或多 Agent。

并发示例：

```text
阅读材料 A ─┐
            ├→ 对比论点 → 形成结论 → 交付
阅读材料 B ─┘
```

两个阅读节点可由根 Agent 并发工具请求，也可在材料很长、需独立分析时委派两个子 Agent。汇总等两边所需结果完成后执行；证据不全时标记部分结果，不装作两边都已核验。

Agent 数、图粒度和并发度按预算与证据调整。失败只重做受影响节点；新事实触发版本化 PlanPatch。简单任务不会因为有 run_id 而自动创建复杂 DAG。

## 3. 会话长期绑定的子 Agent

### 3.1 定义与运行实例

`AgentDefinition` 是可持久保存的角色配置；`AgentInstance` 是一次任务中的实际执行者。绑定会话意味着后续回合能发现该定义，不意味着持续运行、永久保留完整临时上下文或预先占用模型进程。

定义字段：definition_id、owner_id、conversation_id、名称/描述、职责和排除范围、调用条件、技能引用、允许工具类别/权限上限、模型政策、输出契约、默认预算、版本、enabled、创建输入引用。scope 默认 conversation；以后可显式复制/提升到 project 或 personal。不同会话不自动看到彼此子 Agent 定义。

实例字段：instance_id、definition_id/version、parent_agent_id、task/run/node_id、输入引用、实际权限、ResolvedModelPolicy、context_snapshot、workspace_branch、状态和预算。每次运行固定定义版本，更新定义默认影响下一实例；显式撤销权限会阻止旧实例的后续敏感动作。

### 3.2 自然语言创建链路

用户输入“创建论文分析、代码实验、独立审查三个子智能体” → LLM 提出结构化 AgentDefinition 集合 → Agent Runtime 检查职责、名称/ID、工具/技能存在性、scope 和可授予权限 → 持久化到当前会话 Registry → 输出创建结果与配置变更 Item。

已授权、可逆的配置创建不必再要求用户重复批准；指定未知工具、超出当前权限、不可用模型或模糊覆盖已有定义时，明确返回待确认部分，不静默授予。LLM 生成的是配置，执行引擎仍使用 AgentFactory；自定义脚本必须走技能/工具与沙箱，不凭配置字符串直接在服务端执行代码。

采用当前主 Agent 按需加载的 [精炼子 Agent 设计提示词](prompts/agent_definition.md)，通过 `agents.create` / `agents.update` 工具提交配置，统一经 Tool Runtime 调用 Agent Runtime 的定义入口；实际启动另用 agents.invoke。Model Runtime 校验名称/别名、可用性和能力；指定模型缺失时以类型化反馈返回当前 LLM，由它解释、在用户替代授权内修复或请求选择。无需固定的多模型处理流程；未知模型不能未经授权改为继承或 Auto。批量独立定义可部分成功，失败项不启用，幂等状态避免重复创建。完整工具目录和基础发现入口见 [CONTROL_TOOLS.md](CONTROL_TOOLS.md)。

下次请求时，Context Runtime 装入可见子 Agent 的名称、职责、调用条件和权限摘要；根 Agent 可选择委派，也可响应用户明确指定。工具向量索引检索 ToolSpec，子 Agent 定义由独立 Registry 检索；不会把子 Agent 冒充一个普通外部工具。定义大量增长后才考虑额外语义索引，并保留精确名称发现。

### 3.3 隔离与协作

多个实例即使来自同一定义，临时上下文、可写工作区和预算也独立。实例只获得当前任务相关引用；旧任务内容通过 Context Runtime 按允许范围召回，不能直接共享上一次完整 prompt。实际权限取用户、产品、父 Agent、定义和当前环境的交集；子 Agent 无权创建更高权限的后代。

子结果用 NodeResult 交给父 Agent，按依赖显式共享证据。并行写文件使用分支/隔离目录；工具外部副作用用单独幂等与并发限制。定义绑定 Conversation，结果绑定 Task/Run；同一个定义可服务多个任务，但不会把任务结果混成定义自身的状态。

用户可自然语言修改、停用、复制或删除定义。变更记录有旧/新版本、来源 Turn、差异和生效时点；撤销配置产生新修订，不抹去历史。停用影响新调用；删除是否取消已运行实例必须明确，默认不伪装成已经取消旧执行。

## 4. 模型继承与显式覆盖

用户选具体模型 A：根 Agent、子 Agent、Planner/Reviewer 和任务理解/执行判断默认都用 A。仅用户明确说“这个子 Agent 使用 B”或在配置 UI 明确选择 B 时，给该定义保存 `model_policy=explicit(B)`。角色职能差异仍影响工具、技能、上下文和能力校验，不自行改变用户模型选择。

```text
有用户显式子模型覆盖 → 使用覆盖政策
没有覆盖              → 继承最近父实例的有效政策
根实例                → 使用本 Run 固定的会话政策
```

指定子模型 B 的后代默认继承 B，用户可再明确覆盖；独立 Planner/Reviewer 继承所属父 Agent 的有效政策。会话里的持久定义保存 `inherit`，不在创建时把 A 写死；因此用户下回换会话模型 C，未覆盖的子 Agent 随之使用 C。

用户选择 Auto 时，才由 Model Runtime 在继承 Auto 的范围内选择模型；用户对某个子 Agent 明确设置 Auto 也构成可路由的局部范围。具体模型模式下不可用/能力不足时重试或说明缺口，由用户决定是否改模型；不为降低成本或修复故障擅自换模型。既有角色候选列表不得排除固定模型后暗中选另一个；应显示能力校验结果。

每次调用记录模型、政策来源（会话/用户子覆盖/继承）、resolved revision 和实际用量。用户修改模型默认下个 Run 生效，当前 Run 的模型政策不被后台配置更新悄悄改变；明确要求当前修改时走 steer 控制并在安全边界应用。

Agent 文本模型继承不等于把 OCR、embedding、解析器等工具实现也强行改成同一模型；这些专门实现分别配置，并在工具/成本信息中可追溯。

## 5. 查看变更、撤销与保留用户修改

支持两类变更历史：工作区文件/产物由 Workspace Runtime 管理，子 Agent 配置由 Agent Runtime 管理；Run Runtime 持久化 Item、用户选择和引用。

每个 ChangeSet 记录基础/结果版本、来源 Run/Agent/Turn、增加/修改/删除、旧/新内容引用和验证结果。文本支持 diff；结构化文档格式适配器可支持位置或对象级对比，不具备块级能力时提供整版预览/恢复。命令运行也可能改文件，受控工作区需采集执行前后快照或变更清单，不只记录显式 edit 工具。

撤销链路：用户选一个文件/块/变更集/配置修订 → 校验目标与当前版本 → 未合并改动丢弃隔离 ChangeSet；已合并改动生成反向 ChangeSet → 当前版本已被用户修改则三方比较/冲突处理 → 验证并生成新版本 → 记录 revert Item。撤销不能直接把整个目录强制恢复到旧快照而覆盖用户后续编辑。跨步骤依赖时先说明受影响成果，必要时失效并重做对应节点。

用户可选择“保留已有文件，只重新做结论/某段代码”，此时只作用于选定交付单位。撤销后的 redo 也是版本校验后的新修改。历史回退、Run 恢复和外部补偿分别管理；邮件/发布/外部数据库修改仅在具体工具支持补偿且权限允许时可撤销。

## 6. 对话历史：第一阶段建议云端权威，本地缓存

首版已确认支持已连接本地项目读写与测试；执行文件位置与聊天历史位置是独立设置。历史权威存储的以下选择仍为建议：网页账号阶段以云端历史为权威；本地客户端模式可用本地 HistoryRepository 为权威、显式云同步。蓝图中的本地项目并不擅自确定历史已经本地或云端保存。

| 模式 | 历史权威存储 | 本地职责 | 项目关联 |
| --- | --- | --- | --- |
| 首阶段网页账号模式（建议） | 服务端账号空间 | 草稿、近期消息/Item 缓存、同步 cursor | 可选云端 project_id，与浏览器机器路径无关 |
| 后续本地项目模式（预留） | 本地应用或运行服务的 History Repository | 完整事件/定义/引用与文件访问 | project_id + device/root 绑定 |
| 显式云同步（预留） | 作用域明确的同步协议 | 离线副本/待提交命令 | 多设备 root 映射同一个稳定项目身份 |

只靠网页本地缓存无法承担可靠 Run 恢复、账号跨设备历史和服务端子 Agent 绑定；云端权威记录能让这些对象保持一致。本地缓存可清理或被浏览器回收，不能作为已确认执行/审批的唯一记录。

### 6.1 Repository 与同步边界

Run Runtime 内 `HistoryRepository` 提供 append/list/snapshot、控制记录与 AgentDefinition 持久引用；Cloud/Local 实现共享有版本契约。Conversation、Turn、Item、AgentDefinition、Task 和 Project ID 的语义不随存储位置变化。产物本体及代码文件由 Workspace/Asset Repository 管理，历史只存必要引用和快照元数据；不能把所有文件复制成聊天文本。

网页模式：服务端原子写入已接收输入、配置修订和事件编号；客户端按账号+作用域隔离缓存，根据 cursor 同步并用版本比对。离线草稿标记未发送；联网后是否发送遵循用户实际发送动作与幂等键，不能把离线草稿误当已获执行许可。退出账号/切换账号清理或隔离缓存；授权撤销/删除形成 tombstone 并使相应派生索引与缓存失效。

执行状态和聊天展示缓存独立。浏览器关闭不删除服务端 Run；后台是否继续取决于 Run 生命周期和用户设置。已完成/失败/未决副作用状态从权威记录恢复，不能靠前端最后一条“努力奔跑中”文本猜测。

### 6.2 本地项目绑定

Project 使用稳定 `project_id`，显示名称可以修改。机器目录是 `ProjectRootBinding`，包含设备、规范化绝对路径、仓库/工作区身份与权限；路径不充当用户身份或唯一项目 ID。改名、移动目录要重新确认绑定；同名目录不合并历史，不同机器路径可显式映射同一项目。

浏览器本身不默认具有任意本地执行能力；首版通过本地客户端或已配对执行服务接入 Workspace Runtime，用户明确绑定项目和能力范围。项目历史可在应用数据区保存元数据并链接项目，不必把全部聊天写入可提交代码目录；可导出项目规则和 Agent 定义另行由用户选择。

本地历史模式与模型推理位置是两项设置：本地保存聊天不自动意味着模型也在本机运行。使用远端模型时按模型请求与工具政策传输必要内容；云同步则另外控制。跨模式迁移显式导出/导入 ID、版本和可迁移引用，先标记仍需重新授权的账号/文件，避免复制授权或形成两份未协调的权威记录。

## 7. 首批验证用例

1. 短问题首次模型调用就可回答，不额外启动规划/子 Agent。
2. 长但紧耦合任务选择单 Agent + steps；独立材料比较可升级 parent_child + dag + parallel。
3. 信息不足先读取目录/材料，复评后升级，不自动无限使用最高规格。
4. 自然语言创建三个会话子 Agent；新回合可发现，别的会话不可自动看到；权限不超父边界。
5. 会话选 A，全部 Agent 默认 A；显式子模型 B 只影响该子树；下回会话改 C，inherit 定义随 C。
6. 同一子定义的并行实例临时上下文与可写文件互不污染。
7. Agent 修改之后用户又修改同一文件，撤销 Agent 改动保留用户新内容或报告冲突。
8. 网页重连/换设备可恢复权威历史与定义，本地缓存被清理不会丢服务端状态。
9. 项目目录改名、同名项目、迁移和账号退出不导致历史或权限串用。

上述是设计验收场景，尚未实施测试。下一步字段级协议可从 ExecutionAssessment、AgentDefinition/Instance、ResolvedModelPolicy 和 HistoryRepository 开始。
