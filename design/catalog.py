"""Authored component strategies. Build scripts never infer algorithms from labels."""

BASES = {
 "ui": "apps/web/src/features/workspace",
 "ingress": "src/uaw/api",
 "intent": "src/uaw/intent",
 "agent": "src/uaw/agent",
 "context": "src/uaw/context",
 "tool": "src/uaw/tool",
 "workspace": "src/uaw/workspace",
 "model": "src/uaw/model",
 "run": "src/uaw/run",
 "support": "src/uaw/shared",
}

MODULES = {
 "intent": {
  "owner": "TaskFrame与草稿预览；用户原文只从Run读取。",
  "entry": "IntentRuntime.preview(DraftRequest)、understand(UnderstandingRequest)、revise(FramePatchRequest)",
  "strategy": "原文读取→语义解析→按需指代/只读探查→歧义处理→TaskFrame。草稿预览单独只读分支。Semantic Parser可以复用主Agent首次调用结果，不要求一个完整理解流水线先跑完。",
  "ports": "HistoryReader、ContextFacade、ToolReadOnlyPort、ModelFacade、FrameRepository、EventSink",
  "models": "preview/parse使用用户选定模型；歧义语义可在同次调用判断。来源读取、版本CAS和权限由代码执行。",
  "gate": "第一条任务验证原文不可覆盖、歧义与资料读取失败；预览失败不影响发送。",
 },
 "agent": {
  "owner": "Agent定义/实例、TaskGraph、TaskBoard、ControlLease和完成协调。",
  "entry": "AgentRuntime.define_agent(DefinitionRequest)、start(AgentRequest)、step(StepRequest)、delegate(DelegationRequest)",
  "strategy": "根实例单循环起步，工具发现中同时提供会话Agent摘要。用户持久创建角色用create，实际运行用invoke。语义评估分别决定规划/委派/并发，Scheduler执行硬依赖/资源约束，Join核对子结果，Completion Controller提出真实版本完成提案。",
  "ports": "ContextFacade、ToolFacade、ModelFacade、RunBudgetPort、WorkspaceFacade、Definition/Instance/Plan/BoardRepository",
  "models": "决策、角色设计、规划、技能选择和语义核验由继承模型提出；工厂、DAG校验、CAS、控制权与预算由代码落实。",
  "gate": "同预算单Agent基线，验证create不启动实例、invoke不污染上下文、父模型继承、子失败与取消传播。",
 },
 "context": {
  "owner": "ContextSnapshot/Manifest、Task资料派生索引、Memory版本和Reference/Citation。",
  "entry": "ContextRuntime.build(ContextRequest)、ingest(IngestionRequest)、remember(MemoryWriteRequest)、forget(ForgetRequest)",
  "strategy": "来源/规则、资料索引、记忆是独立支路；按purpose与模型预算合流。来源经授权解析、版本发布后检索；记忆候选经用途/冲突核验；选择/压缩保护关键要求；Composer生成当前调用快照。",
  "ports": "HistoryReader、BoardReader、WorkspaceReader、SourceProvider、ModelFacade、CachePort、Index/Memory/ReferenceRepository",
  "models": "查询生成/语义选择/记忆提炼/压缩按需使用当前模型；结构解析、访问过滤、版本发布与删除由代码执行。embedding模型是独立工具能力。",
  "gate": "真实材料定位、权限内检索、删除传播、关键数字压缩保护及输出空间保留。",
 },
 "tool": {
  "owner": "ToolSpec、调用attempt/效果账本、提供方健康与MCP协议session。",
  "entry": "ToolRuntime.discover(DiscoveryRequest)、invoke(ToolCall)、reconcile(ReconcileRequest)",
  "strategy": "发现支路缩小候选并向LLM暴露schema；调用支路校参数→预检→必要审批→复核→意图→派发→规范结果。失败恢复有界且只自动切明确等价能力。MCP和内部控制工具均经过同一闸门。",
  "ports": "ConfigurationReader、ApprovalPort、BudgetPort、Workspace/Agent/Context/Model控制工具适配器、ProviderAdapters、EffectRepository",
  "models": "选择哪个工具由Agent当前模型决定；注册、发现过滤、闸门、重试/熔断与对账由代码。非等价替换反馈Agent再判断。",
  "gate": "schema与权限分离，审批后资源变更复核，未知写先查状态，MCP撤销与大结果分页。",
 },
 "workspace": {
  "owner": "项目绑定、基础快照、隔离分支、环境/进程、ChangeSet、Artifact/ReviewSet。",
  "entry": "WorkspaceRuntime.allocate(WorkspaceSpec)、prepare(EnvironmentRequest)、merge(MergeRequest)、review/revert(ChangeRequest)",
  "strategy": "本地绑定明确设备/根与能力；基础状态包括获准未提交修改；并行写隔离，原生模式明确权限；真实环境ready后执行并采集改动；合并/局部接受/撤销核对用户当前版本，再形成受控成果和重验。",
  "ports": "LocalRunnerClient、CloudSandboxAdapter、Policy/BudgetPort、ProcessExecutor、Snapshot/Change/Artifact/ReviewRepository、FormatAdapters",
  "models": "代码写作与冲突修复方案由Agent提出；实际文件/进程、三方合并、范围与版本检查由代码，语义冲突无法确认交用户。",
  "gate": "Runner越界、未提交内容快照、shell改动采集、真实test退出码、用户改动保留与撤销。",
 },
 "model": {
  "owner": "ResolvedModelPolicy、模型调用attempt/实际配置/usage；配置目录来源归控制层。",
  "entry": "ModelRuntime.resolve_policy(PolicyRequest)、list(CatalogRequest)、generate(ModelCall)",
  "strategy": "先继承用户模型意图，再核对目录/能力，只有Auto授权才选择候选。Gateway预留预算并调用provider adapter，输出校验与usage结算覆盖失败attempt，Recovery遵守固定/Auto政策。",
  "ports": "ConfigurationReader、CredentialReader、RunBudgetPort、ProviderAdapters、CallRepository、TraceSink",
  "models": "该模块执行模型调用，不要求额外模型来选模型。Auto策略可按受评测规则选择或请求语义建议，但不能覆盖固定模型。",
  "gate": "模型继承树、明确子模型缺失反馈、协议不支持、流式重试、usage去重与固定模型不暗换。",
 },
 "run": {
  "owner": "不可变用户输入/历史、RunState、Items/Event、BudgetLedger、审批/控制与checkpoint/lease。",
  "entry": "RunRuntime.create(RunRequest)、control(ControlRequest)、decide_approval(ApprovalDecision)、checkpoint/resume(RecoveryRequest)",
  "strategy": "受理保存原文与轻量Run，关键变化追加Item/Event。预算预留/结算共享总额，用户控制安全边界注入。checkpoint引用领域版本；恢复租约→兼容→当前访问→Tool效果对账→Workspace版本→继续。取消聚合真实执行器回执。",
  "ports": "History/Run/Event/Budget/Approval/CheckpointRepository、Agent/Tool/Workspace控制接口、ConfigurationReader、EventTransport",
  "models": "状态机、账本、恢复、取消与事件都由代码。assisted代审调用独立Reviewer且继承模型，决定只在预授权范围有效。",
  "gate": "重复受理、事件重连、双预算预留、拒绝/撤销、崩溃恢复及completed与succeeded分开。",
 },
 "support": {
  "owner": "共享缓存派生项、平台配置/账号凭据、扩展包ReleaseManifest、诊断Trace与离线评测集/报告。",
  "entry": "Configuration.publish、Extension.activate、Cache.get_or_compute、Observability.observe、Evaluation.evaluate",
  "strategy": "提供独立支撑接口，领域通过ports消费；常规版本固定与当前撤销分开。缓存负责机械复用，语义有效性归领域；观测记录实际版本/attempt，评测固定初态/权限/fixtures对比发布候选。",
  "ports": "各领域的失效/诊断接口、CredentialStore、RepositoryAdapters、隔离评测执行器、人工作业入口",
  "models": "共享设施不逐请求固定调用LLM；语义评分按评测配置调用且人工校准，不授予工具执行权限。",
  "gate": "无凭据泄漏、缓存失效、诊断不替权威日志、发布不可变版本与真实写评测禁重放。",
 },
}

MODEL_STAGES = {
 "intent.preview", "intent.semantic", "intent.ambiguity", "agent.definitions", "agent.loop",
 "agent.assessment", "agent.planning", "agent.skills", "agent.completion", "context.retrieval",
 "context.memory", "context.selection", "context.compression", "agent.completion.contract",
 "agent.completion.semantic", "context.memory.candidate", "context.memory.conflict", "support.evaluation",
}

SOURCES = {
 "intent": [("Context · 按目的装配/来源", "3ec6ccd32c87802fb6c2c7dd51db660d"), ("Runtime · 状态与循环", "3f06ccd32c878070921ce42ff22e6257")],
 "agent": [("Multi-Agent · 角色/路由/委派/上下文", "3ec6ccd32c8780d6b4f9d357a257bfd9"), ("Planning · 分解/依赖/修订", "3ec6ccd32c8780cb836cce28bd809d12"), ("Skills · 发现/加载/权限", "3ec6ccd32c87807bb032da89a48c45ae")],
 "context": [("Context · 预算/压缩/选择", "3ec6ccd32c87802fb6c2c7dd51db660d"), ("Memory · 冲突/删除", "3ec6ccd32c87803db411c4c48b832941"), ("RAG · 更新/权限", "3d66ccd32c87806894a2ec48969c200a")],
 "tool": [("Tool · 调用/MCP/效果", "3e96ccd32c8780fab75dd0b4c21fe7fb"), ("Guardrails · 审批/复核", "3f06ccd32c878056b729e7a41fd4232b")],
 "workspace": [("Runtime · 执行环境/恢复", "3f06ccd32c878070921ce42ff22e6257"), ("Guardrails · 沙箱/本地边界", "3f06ccd32c878056b729e7a41fd4232b")],
 "model": [("Model Strategy · 继承/能力/adapter/usage", "3ec6ccd32c87807bb032da89a48c45ae")],
 "run": [("Runtime · 预算/deadline/checkpoint", "3f06ccd32c878070921ce42ff22e6257"), ("Guardrails · durable审批", "3f06ccd32c878056b729e7a41fd4232b")],
 "support": [("Cache · 在途合并/失效", "3ec6ccd32c87809fbf70ea46b440a3e3"), ("Evaluation · 样本/版本/Trace", "3ec6ccd32c87805596bad437d733ecf9")],
 "ui": [("Runtime · 用户交互/控制", "3f06ccd32c878070921ce42ff22e6257")],
 "ingress": [("Runtime · 受理/身份/状态", "3f06ccd32c878070921ce42ff22e6257")],
}

# Each row: payload fields, ordered decisions, persistence/consistency,
# failure response, cache/resource handling, acceptance examples.
STRATEGIES = {}


def add(id, payload, steps, commit, errors, efficiency, acceptance):
    assert id not in STRATEGIES
    STRATEGIES[id] = dict(payload=payload, steps=steps.split("；"), commit=commit,
                         errors=errors.split("；"), efficiency=efficiency,
                         acceptance=acceptance.split("；"))


add("ui", "conversation_id: ID; draft_revision: int; selected_project_ref: Ref?; last_event_seq: int",
 "输入保持用户原文，预览请求另带draft_revision；发送使用稳定turn_request_id，反馈丢失先查询发送状态；按Item ID/revision更新消息，工具、审批和变更用结构化卡片；重连先续事件，缺序或revision不匹配拉取权威快照；用户评论和局部接受绑定实际产物版本，不把当前屏幕文本当资源版本",
 "草稿可短期本地保存；Run/审批/成果以服务端或已明确的历史权威为准，缓存不提交执行状态。",
 "草稿旧响应丢弃；未知Item类型展示通用内容；旧版本审阅返回stale并显示差异，不默默接受",
 "节流/取消预览并去重流事件，隐藏技术细节不丢可展开真实记录。",
 "断线重连不重复展示/执行；旧预览不覆盖新草稿；用户修改文件后旧接受操作被阻止")
add("ingress", "request_id: ID; original_text: str; attachment_refs: list[Ref]; conversation_id: ID; expected_task_revision: int?",
 "传输层只解析协议和大小，不加工用户目标；准入检查主体、配额、请求幂等和资源归属；资源解析只生成已授权Reference，不相信客户端绝对路径；向Run追加原文并取得不可变InputRef；装配AgentExecutionRequest及用户模型意图引用，再创建Run与事件订阅",
 "request_id+主体绑定同一受理结果；原文追加和本地Run创建使用事务或可恢复的受理意图。",
 "重复请求返回既有Run；越权资源拒绝且不透露其详情；受理未完成可查询pending，不新建第二Run",
 "请求大小和活跃Run有界；附件不经文本请求内联传递大二进制。",
 "重发创建一个Run；篡改conversation归属被拒绝；本地路径字符串不授予访问")

add("intent.preview", "draft_ref: Ref; draft_revision: int; preview_budget: Budget; model_policy_ref: Ref",
 "读取当前草稿与最小最近上下文；使用会话选定模型产生一两句目标摘要，只声明理解和假设；草稿变更取消旧任务，新请求保留自己的revision；输出DraftPreview及依据引用，不持久为正式TaskFrame",
 "预览是可淘汰派生记录；发送原文后重新理解，预览只作为可比较参考。",
 "模型失败返回preview_unavailable，正常发送继续；取消返回cancelled，不显示错误任务理解",
 "节流时长可配置且不阻塞发送；仅相同草稿、规则和模型版本复用。",
 "快速连续输入只显示最后revision；预览无工具写操作；具体模型模式不换廉价模型")
add("intent.original", "original_input_ref: Ref; user_patch_refs: list[Ref]",
 "向Run History读取原始用户输入及明确修订；校验作用域、内容版本和资源可访问性；保留原文顺序和每项来源；返回只读输入集给语义解析，不将AI预览混入用户指令",
 "只读原文，不维护第二份可修改账本；纠正必须先成为新的用户输入记录。",
 "缺失引用返回input_missing；版本不匹配回取权威记录；已删除资料返回不可用状态",
 "不可变原文块按版本短期复用，读取仍检查当前访问范围。",
 "模型改写不覆盖原文；用户纠正保持可追溯；旧checkpoint不能复活已撤销内容")
add("intent.semantic", "input_refs: list[Ref]; instruction_set_ref: Ref; material_refs: list[Ref]",
 "让当前模型提取目标、约束、交付物与未知项；每个硬要求绑定用户来源，推断标记assumption；通过结构schema验证，再核对未被遗漏的显式要求；信息不足返回所需材料或候选解释；已有充分理解时合并首次Agent调用，避免固定额外分类模型",
 "解析结果提交新理解版本；原文不变，重大目标变化向用户显示。",
 "结构错误有界修复；目标互相冲突返回ambiguity；证据不足不填成确定事实",
 "用相关上下文而非全历史，解析成本进入该Run预算。",
 "短请求可以直接答复；复杂度不按词典决定；金额/日期等硬条件不被摘要遗漏")
add("intent.references", "expressions: list[str]; candidate_scope: Scope; expected_versions: dict[ID,int]",
 "先使用用户明确选中资源和精确ID；再查当前会话/项目最近相关引用；按语义与位置形成候选并附依据；唯一且足够可靠的候选解析为Reference；关键动作出现多候选交歧义策略，不凭相似文件名任选",
 "TaskFrame只记录已解析引用及版本；候选是临时数据，授权由resolver复核。",
 "断开的本地Runner返回source_disconnected；多个候选返回ambiguous_reference；不可定位返回reference_missing",
 "候选数与读取大小限制；同名匹配结果不能作为跨项目缓存键。",
 "两个同名文件不会写错；‘上次方案’可以追溯版本；用户选择来源优先于语义猜测")
add("intent.probe", "missing_facts: list[str]; allowed_scope: Scope; max_calls: int; deadline: Timestamp",
 "把缺口转成最少的资料读取需求；优先Context已有来源，再发现允许只读工具；预留预算并通过Tool调用，禁止创建工作区写入；收到信息后核对是否消除缺口；达到探查额度仍未知则交Agent调研或澄清",
 "保存证据引用和探查结果，不修改用户目标或外部状态。",
 "工具权限失败直接返回；来源读取失败明确区分为空与读取失败；预算超限保留unknowns",
 "同权限域只读结果可复用，探查不得取得新的完整任务预算。",
 "理解阶段不会安装依赖；失败资料不当作无内容；两次读取仍未知能转交主循环")
add("intent.ambiguity", "interpretations: list[Interpretation]; impact: Impact; reversible: bool; unresolved: list[str]",
 "逐项区分非关键表达与影响动作后果的歧义；已有来源能够排除候选时回填依据；低影响可逆行动带假设开始；无法安全选择的关键条件提出一组简短澄清；决策随新材料和用户输入复评",
 "澄清进入Run InteractionItem，用户回答是新输入；假设保持显式版本。",
 "用户未回复只保留waiting，不能视为默认同意；澄清回答不匹配原问题返回待解析",
 "合并相关缺口避免连续提问，不用固定置信阈值替代后果判断。",
 "格式偏好不阻塞只读调研；不确定发布账号必须澄清；假设被纠正会使相关结果失效")
add("intent.frame", "goal: str; constraints: list[Constraint]; output_specs: list[OutputSpec]; evidence_refs: list[Ref]; expected_revision: int",
 "收集语义解析、已定位资源、保留假设和未知项；验证硬要求都有用户/政策来源；生成TaskFrame候选并比对旧版本；用expected_revision提交新版本；只标记受变更影响的理解字段，交Agent决定计划失效范围",
 "Intent是TaskFrame唯一写入者；版本追加，Run记录frame_ref和变更事件。",
 "CAS冲突返回当前frame revision；来源缺失不提交伪完整frame；重大目标歧义保持pending",
 "无实质变化时复用原版本，不能把时间戳变化造成全部任务重规划。",
 "原文仍可读取；用户目标修订不会静默覆盖；同一输入重复生成不乱增revision")

add("agent.definitions", "definitions: list[AgentDefinitionDraft]; batch_policy: atomic|independent; source_input_ref: Ref; expected_version: int?",
 "主Agent识别用户创建/修改意图，按需加载agent_definition短方法；通过agents.create/update提交职责、use_when、avoid_when、技能工具边界和模型意图；Tool注入主体/会话与幂等键；Agent Registry检查作用域、名称冲突、依赖与用户授权，Model解析inherit/explicit/auto；按整组或独立项策略提交不可变定义版本；定义成功后返回可发现摘要，实际执行另走agents.invoke",
 "唯一name约束绑定owner/conversation；每项client_definition_key保持重试幂等。更新CAS，停用/撤销产生新版本；工厂固定定义版本。",
 "模型不存在返回当前LLM且不启用；同名返回conflict，不覆盖；原子批量任何一项失败全组不提交",
 "常驻只提供摘要，长指令/技能按需加载；配置创建不预留子执行预算。",
 "创建两个角色不启动两个任务；重复请求不重复创建；未显式指定的模型均inherit")
add("agent.loop", "instance_ref: Ref; observations: list[Ref]; current_frame_ref: Ref; remaining_budget: Budget",
 "读取当前用户修订与实例状态；Context按agent_step装配实际可用定义/工具摘要；当前继承模型提出答复、发现、调用、规划或委派；对动作进行生命周期/预算检查，工具动作统一交Tool；消费实际ToolResult或子结果而非模拟成功文本；有新约束先失效受影响状态，再决定下一步或申请完成",
 "每个实例只提交自己的版本化状态；关键观察引用保留，Run存checkpoint引用。",
 "模型协议错误交Model恢复；工具错误消费类型结果；重复无进展或额度耗尽交付部分/询问，不无限循环",
 "按需取上下文，不每轮重复完整角色定义；决定与结果分离计量。",
 "单次问答不生成DAG；工具失败不会被跳过；steer在安全边界影响下一动作")
add("agent.assessment", "task_frame_ref: Ref; capability_snapshot: Ref; existing_agent_refs: list[Ref]; decision_question: str?",
 "按原文、独立子成果、依赖、风险与可用能力作语义评估；分别输出planning_level、delegation、parallelism及信息缺口；附可验收子目标和预估协调/等待成本；Runtime检查预算、最大深度、flag与资源上限；证据不足以证明委派收益时保持单Agent，运行中可根据失败/新材料复评",
 "Assessment是建议记录，不直接创建实例或把全部步骤标记ready。",
 "不支持能力返回capability_gap；schema错有界修复；超预算建议被拒绝并回LLM缩小计划",
 "允许合并到首次理解；不强制独立判断Agent或强模型。",
 "长但强耦合任务仍单Agent；两个独立来源可只并发工具；没有预算不能启动多Agent")
add("agent.planning", "planning_level: steps|dag; node_specs: list[NodeSpec]; patch: PlanPatch?; expected_plan_revision: int",
 "步骤模式记录目标与验收，不强行建依赖图；DAG模式检查引用、环、依赖完备和输出契约；估计所需工具/角色及可用预算，计算资源冲突；PlanPatch验证已完成节点不变量并计算受影响闭包；CAS发布新计划版本，Scheduler只消费有效版本",
 "Agent拥有计划版本；已完成结果保留历史引用，受影响节点变stale。",
 "循环依赖返回cycle_path；缺输入返回missing_dependency；CAS冲突不自动覆盖新用户计划",
 "未知未来细节使用高层节点，准备就绪再展开，避免规划全部臆测步骤。",
 "同版图无环；用户改一个结论仅重做依赖它的节点；规划成功不等于任务完成")
add("agent.scheduler", "plan_ref: Ref; node_states: dict[ID,State]; available_resources: ResourceSnapshot; expected_revision: int",
 "找依赖已满足且结果版本有效的节点；核对权限、deadline、工作区写冲突与总预算；按就绪节点与受控优先级预留资源并取得租约；选单Agent步骤、并发工具或子实例执行，不把节点强制映射Agent；完成/失败后重新计算就绪集合并触发Join条件",
 "领用与预留使用一致提交或可恢复分配意图；完成提交携带node attempt和lease版本。",
 "资源不足返回queued且等待有界；依赖failed/stale阻止调度；过期租约完成回执不能覆盖新attempt",
 "并发上限覆盖子Agent，不为每个Run独立给无限worker；维护就绪队列而非轮询所有节点。",
 "两个写同目录节点不直接并行；双领只能一个有效提交；上游失败不启动必需下游")
add("agent.collaboration", "delegation_spec: DelegationSpec; operation: delegate|join|handoff; expected_control_revision: int?",
 "默认子Agent只返回结果，父保持用户对话控制；为可独立工作定义目标/输入/输出/验收/预算；工厂固定角色定义和继承模型，Context按引用隔离；通道只共享必要结果与证据；Join核对每个必需结果状态和版本；真正移交对话时另用ControlLease，先核对未决动作与权限再CAS交接",
 "Agent拥有实例树、消息协议、TaskBoard与ControlLease；Run追加关联事件和恢复引用。",
 "子失败回父选择缩小/重派/部分交付；缺失输入不Join；handoff失败保留旧控制者或明确等待",
 "共享摘要+原始受控引用，限制深度/扇出/互聊次数；所有资源计入父Run。",
 "子角色继承主模型；兄弟不共享临时prompt；任何时点有效最终对话控制者唯一")
add("agent.skills", "skill_query: str; skill_refs: list[Ref]; target_role: ID; template_ref: Ref?",
 "用任务目标比对可见名称/描述与排除条件；加载主指令前校验版本、来源、依赖、权限与循环；固定包内容hash后按需请求Context读取参考；脚本必须作为Tool动作在获准环境运行；模板固定口径/步骤与动态范围，变更需用户授权；记录激活版本与实际验收结果",
 "Registry/ActivationLedger归Agent；包发布归Extension，装配块归Context。",
 "缺必需依赖停在安全阶段；循环加载返回cycle；撤销阻止后续执行，旧版本不能越权继续",
 "三层加载：元数据、主方法、按需资源；不把全部包长文本常驻。",
 "关键词相同不硬套Skill；安装包不授予权限；升级仅影响新激活且可定位旧运行版本")
add("agent.completion", "delivery_contract_ref: Ref; artifact_refs: list[Ref]; verification_refs: list[Ref]; expected_revisions: dict[ID,int]",
 "从原文和用户修订确认必需目标；按当前证据动态选择真实检查，不运行固定Twitter字段校验；语义评审区分满足/缺口/未验证；Runtime核对真实成果、检查版本、硬条件和未决效果；用CAS提交CompletionProposal到Run；Workspace交付并独立追踪用户接受",
 "Agent拥有验证协调报告与提案；Run拥有终态，Workspace拥有真实产物与ReviewSet。",
 "旧报告返回stale并选择受影响重验；必需检查失败不能succeeded；未决外部写阻断依赖完成",
 "简单答复轻量核对；Reviewer按任务需要，不强制每次另起Agent。",
 "没运行测试不能报通过；合并后核验实际新版本；用户不接受不被AI自动标记accepted")
add("agent.board", "entry_key: ID; result_ref: Ref; expected_board_revision: int; provenance: list[Ref]; status: candidate|confirmed",
 "按字段/节点写入所有权检查提交者；验证结果schema、来源、任务目标版本和授权；以expected_revision CAS提交引用；变更后计算真正依赖该条目的节点集合；将受影响结果标stale并向Scheduler发送事件",
 "共享板只存协调状态与可审阅引用；局部scratch与隐含推理保持实例私有。",
 "冲突返回当前条目和revision，按目标重读再提交；未验证候选不冒充confirmed；权限失败不共享",
 "按依赖订阅相关条目，CAS冲突率驱动粒度调整，不一开始分布式全局锁。",
 "并发两个不同节点都能提交；旧目标结果不能覆盖新目标；临时私密内容不进入共享板")

add("agent.factory", "definition_ref: Ref?; role_profile_ref: Ref?; delegation_ref: Ref; creation_key: str; parent_agent_ref: Ref?",
 "检查获准定义或临时角色版本与目标契约；校验模型政策、有效权限、深度与实例总数；预留子预算并分配私有上下文/必要工作区；持久记录实例与分配意图再调度；重复creation_key查询已有实例，失败回收未用预留与目录",
 "实例只引用固定DefinitionVersion，不修改长期定义；实际分配需可恢复。", "定义不可用拒绝；预留不足不启动；部分资源准备失败明确preparation_failed",
 "只读共享固定快照，避免无必要worktree。", "create不会隐含调用工厂；并发同invoke键只有一个实例；两个不同实例scratch独立")
add("agent.definitions.designer", "user_input_ref: Ref; existing_definition_refs: list[Ref]; visible_capabilities: Ref; design_method_ref: Ref",
 "核对用户持久创建/修改要求；按需加载短角色设计方法与可用能力；当前主模型生成职责/正反调用条件/简短指令与契约；未指定模型保留inherit，工具依赖只从真实目录选择；关键歧义先澄清，否则调用create/update，不强制独立设计Agent",
 "只产生待验证草案，Registry提交成功后才宣布已创建。", "未知能力返回dependency_gap；模糊持久授权不保存；模型不存在保留原意图",
 "Role指令短，长方法放Skill；设计费用计入当前Run。", "创建要求不触发业务任务；临时分工不被永久保存；用户模型名称原样保留")
add("agent.definitions.validator", "draft: AgentDefinitionDraft; user_source_ref: Ref; effective_scope: Scope; existing_names: list[str]",
 "服务端核对owner/conversation及真实用户授权；检查名称唯一、必需职责/契约与指令长度范围；检查可见Skill/tool类别和委派边界；新权限只能请求当前有效交集，越界作为阻碍项反馈；批量依赖先整组验证",
 "ValidatedDraft不是enabled定义，必须交Repository提交。", "重名返回definition_conflict；依赖缺失返回dependency_missing；来源不足返回authorization_gap",
 "相同不可变依赖版本可复用解析，但授权当前复核。", "模型伪造source_ref不能自授权限；同名不静默覆盖；完整批量不会部分提交")
add("agent.definitions.model_intent", "model_request: inherit|explicit|auto; requested_name: str?; source_input_ref: Ref; parent_policy_ref: Ref",
 "inherit不写死当前型号；explicit核对用户原文指定并保留原名称；通过Model目录精确/登记别名解析可见候选；缺失/歧义/不可用返回当前主LLM解释或询问；只有用户授权替代或Auto时选择合法范围后重提交",
 "保存用户模型意图与规范引用，实例创建时再解析实际继承。", "model_not_found不启用；model_ambiguous不猜；未经授权替代拒绝",
 "目录按需读取，固定模式不做成本路由。", "根A未指定子inherit；明确B缺失不能自动改A；下次根C时inherit跟C")
add("agent.definitions.repository", "validated_drafts: list[Draft]; batch_policy: atomic|independent; stable_item_keys: list[str]; expected_versions: dict[ID,int]",
 "以主体/会话/请求及项键核对重试参数；atomic先校验全组并事务提交，independent逐项返回结果；新增保持名称唯一，更新CAS追加版本；启用项进入可发现集合，未解决草稿不能被调用；提交后产生配置变更引用及Run事件",
 "同版本hash不可变，定义未执行；查询pending意图防反馈丢失重复create。", "同键不同参数idempotency_conflict；CAS失败返回当前diff；atomic失败不提交任一项",
 "幂等记录不当结果缓存；摘要索引可异步但发现复核权威。", "重发不重复角色；独立批量准确报告部分成功；未启用草稿不候选")
add("agent.definitions.discovery", "conversation_id: ID; task_goal: str; role_constraints: list[str]; max_candidates: int; definitions_revision: int",
 "按owner/conversation、enabled、flag/权限与能力过滤；小集合直接提供摘要，大集合关键词/向量召回；比对职责、use_when/avoid_when、输入输出与资源状态；返回带版本候选给当前LLM决定自己做/委派；选中后加载长方法，invoke再次复核",
 "候选仅诊断/缓存派生；发现不创建实例、不批权限。", "无候选返回agent_capability_gap；停用/旧索引候选丢弃；跨会话未经授权拒绝",
 "只提供少量短摘要，不每轮加载全部角色。", "一句概念解释不硬调论文Agent；停用立即不可invoke；工具调用与Agent候选分开")
add("agent.definitions.change_service", "definition_id: ID; base_version: int; selected_change_ref: Ref; operation: diff|disable|revert; expected_current_version: int",
 "读取指定定义版本并生成字段/权限/模型差异；撤销在当前版本上构造反向patch；保留之后用户修改，冲突明确返回；新权限/模型覆盖仍核对用户来源；CAS提交新版本并失效定义摘要",
 "反向修订保留完整历史；普通停用仅阻止新实例，安全撤销当前约束后续动作。", "并发编辑返回change_conflict；已发生外部动作不可由配置回退撤销",
 "小配置精确diff，无需语义压缩。", "撤销不抹用户后加职责；已运行代码不被配置回退逆转；模型变更来源可审阅")
MODEL_STAGES.update({"agent.definitions.designer", "agent.definitions.discovery"})

add("context.sources", "source_refs: list[Ref]; purpose: Purpose; source_revision_policy: pinned|latest_required",
 "按来源类型分派到History、TaskBoard、Workspace或账号适配器；读取前检查scope与当前撤销；固定取得的内容版本并核对位置/hash；将已知缺失、断开与可用材料分别返回；登记SourceManifest供后续检索和引用",
 "只写来源清单，源对象由原领域拥有；latest_required取得版本后也固定本次实际版本。",
 "本地断开返回disconnected；无权拒绝；版本不稳定返回source_changed供重读",
 "只读必要片段；缓存键包含来源版本/可见域，临时下载链接不持久当源。",
 "网页摘要与正文区分；当前版本变化可以发现；断开不伪装文件为空")
add("context.rules", "scope_paths: list[PathRef]; user_instruction_refs: list[Ref]; activated_skill_refs: list[Ref]",
 "只从可信注册来源发现规则；用户明确要求优先，项目规则按根到目标目录细化，再装配技能/角色/偏好；记录覆盖关系与内容版本；硬权限始终由Runtime强制，不被自然语言覆盖；不可同时满足的关键要求返回冲突与澄清，普通风格冲突按确定优先级",
 "保存InstructionSet与rule_manifest；跨目录分别记录适用规则，工具写入前核对作用域。",
 "未经注册的网页指令当数据；关键冲突返回rule_conflict；规则变化通知相关上下文失效",
 "规则hash复用解析；按真实目标路径加载，不把整项目所有规则常驻。",
 "网页‘忽略规则’不生效；子目录规则仅在相应目录生效；用户明确纠正可追溯")
add("context.ingestion", "source_ref: Ref; parser_version: Version; chunk_profile: ID; embedding_profile: ID; expected_active_revision: int",
 "校验来源可用与解析资源限额；保留标题/页码/表格结构及定位，产生内容块；按内容hash避免重复处理并构建关键词/向量派生索引；验证块完整性、来源与ACL后CAS切换active revision；删除先让当前访问不可用，再清理块/索引/派生摘要及缓存",
 "新revision构建时不覆盖旧版，发布标记为权威；保留或删除旧内容按用户保留政策。",
 "解析失败标parse_failed，不能假称无结果；索引构建失败不发布；并发新版本返回publish_conflict",
 "增量处理改变的块；配置或embedding版本变化仅重建依赖派生内容。",
 "新旧索引不会混为一版；大文件解析有资源上限；删除后不能通过摘要再召回")
add("context.retrieval", "query: str; corpus_refs: list[Ref]; active_revisions: dict[ID,int]; top_k: int; freshness: FreshnessPolicy",
 "精确引用优先直接读，开放查询才生成检索需求；在授权子集中关键词/向量召回而非全库TopK后删；合并候选并按目标相关、来源时效/权威与覆盖排序；检查证据冲突/缺口，必要时让Agent扩大检索；返回前复核当前ACL与实际版本并输出定位引用",
 "保存RetrievalManifest与实际索引版本；不能把高相似排名写成已验证事实。",
 "索引不可用返回retrieval_unavailable；无命中与读取失败分开；撤销候选不能给模型",
 "召回数、重排调用和内容大小有界；同查询/索引/范围可缓存，命中仍当前复核。",
 "无权文档不进入重排日志；互相矛盾资料保持来源；唯一已选文件可跳过向量搜索")
add("context.memory", "candidate: MemoryCandidate?; selector: MemorySelector?; memory_policy_ref: Ref; expected_revision: int?",
 "区分显式记住与后台推断候选；检查读取/贡献开关、用途、作用域和保留期；按具体槽位/条件查重，用户纠正优先，未决冲突保持待确认；提交新事实版本后才宣告记住；召回时复核有效时间和授权；遗忘立即停止召回并传播到摘要/索引/缓存",
 "Memory记录source、valid_from/to、supersedes与derived_from，Context是唯一写入者。",
 "提交失败如实返回not_saved；低可信研究结论留任务候选；删除部分失败返回待清理项",
 "明确profile槽位可精确读取；仅检索开放经历时使用向量，不每句话写入。",
 "记忆关闭不影响当次原文；‘会Go’不等于‘喜欢Go’；删除偏好不从备份悄悄恢复")
add("context.selection", "candidate_refs: list[Ref]; purpose: Purpose; model_context_limit: int; output_reserve: int; tool_reserve: int",
 "先从模型可用窗口扣除输出/工具反馈/必要压缩余量；用户原文、硬约束与当前未完成状态优先；按来源可信、目标覆盖、时效、成本选择候选；大工具结果先分页/筛选，避免用一次压缩解决无限输入；剩余缺口转压缩或读取需求，不能静默丢关键条件",
 "记录被选/被排除块和原因到ContextManifest，真实用量更新预算估计。",
 "必需内容装不下返回context_insufficient；未知tokenizer使用保守估算并报告；无关块不补满窗口",
 "purpose配置可扩展但不决定固定业务链；保留稳定块身份便于复用。",
 "压缩后仍有输出空间；千页返回不会全塞prompt；必需引用不足明确暴露")
add("context.compression", "input_snapshot_ref: Ref; preserve: PreservationSpec; target_tokens: int; expected_context_epoch: int",
 "固定输入revision并提取必须保留的目标、约束、数值单位、未完成工作和来源；使用当前模型生成ContinuationState；对比保留项并核查证据定位仍有效；通过后CAS发布新context_epoch；失败缩小压缩范围或回读原文，权限/工具状态独立从Runtime读取",
 "保存输入依赖、压缩方法/模型版本与guard结果；压缩不删除可审阅交互历史。",
 "关键数字丢失返回compression_invalid；压缩时用户改目标返回stale；无空间安全停下或请求缩小范围",
 "阶段触发+预算软硬边界，设置冷却避免每轮重压；相同输入/目的可复用。",
 "单位不从万元变元；未决调用不写已成功；用户纠正后旧压缩状态不可用")
add("context.composer", "instruction_set_ref: Ref; selected_block_refs: list[Ref]; capability_snapshot: Ref; context_epoch: int",
 "按可信指令、角色方法、用户原文、必要历史、实时材料分区；稳定共同前缀与schema规范序列化；实际可用工具与会话Agent摘要按权限装配；数据块标来源但不提升信任权限；核对预算与依赖版本后返回ContextSnapshot及Manifest",
 "快照内容不可变；装配源引用保留以便诊断，删除/撤销可使其不可再读取。",
 "依赖stale重新选择块；缺角色必需方法返回dependency_missing；序列化超预算不发模型",
 "动态时间/实时查询放相应后部，不为缓存隐瞒当前时间或权限变化。",
 "同等输入序列化稳定；外部恶意文本不变规则；模型看到的目录与实际可用一致")
add("context.references", "kind: web|asset|content|artifact|workspace|verification|local; source_id: ID; revision: Version; location: Location; claim_anchor: str?",
 "登记实际取得来源的版本、hash、位置与可见范围；Citation单独绑定回答论断位置；打开时按身份调用相应resolver核验当前可访问与位置有效；对于网页摘要明确证据范围；本地引用按设备/项目/版本走Runner，不能直接暴露服务器绝对路径",
 "Reference是来源定位，Citation是论断关系；临时签名链接按读取时生成。",
 "来源删除返回gone；本地断开返回disconnected；定位迁移失败返回location_stale，不编造页码",
 "只取指定片段；可访问不等于支持论断，语义支持交完成核验。",
 "不存在的URL不造引用；过期签名重新解析；文件测试报告定位实际受测版本")

add("tool.registry", "tool_id: ID; version: Version; spec: ToolSpec; provider_ref: Ref; expected_registry_revision: int",
 "校验schema、效果类别、权限、超时、幂等与等价声明；平台启用提供方后注册不可变spec；生成只含允许元数据的关键词/向量表示；索引发布绑定tool_id/version，发现阶段复核权威记录；关闭/撤销先拒绝执行，再异步清理索引",
 "ToolSpec为权威；向量表示可重建，不能储存唯一schema或凭据。",
 "重复同版本不同hash拒绝；schema不兼容返回registration_invalid；索引滞后显式记录不破坏执行授权",
 "批量增量索引；真实调用可用性由当前注册/提供方状态检查。",
 "索引旧工具不能被执行；工具描述不含密钥；名称相似不构成等价契约")
add("tool.discovery", "query: str; role_capabilities: list[ID]; allowed_scope: Scope; max_candidates: int; registry_revision: int",
 "产品flag、主体、角色类别与执行环境先缩小候选；精确工具名优先，无精确意图做关键词/向量召回；按能力/schema适配、健康、成本与描述反例重排；返回少量描述，选中后按需加载完整schema；LLM可扩大范围，但不能扩大授权范围",
 "记录候选与选中理由；目录命中不产生授权记录。",
 "无匹配返回capability_gap；索引失败可退到权威精确/类别检索；无权限候选不泄露详情",
 "小工具集直接候选与向量策略对照；缓存依赖role/flag/registry/访问域。",
 "角色筛选后LLM仍可选择工具；没有候选不发明名字；权限收回立即影响可调用性")
add("tool.invocation", "tool_ref: Ref; arguments: Object; action_id: ID; trusted_context: ToolRuntimeContext",
 "schema规范化与资源引用校验；当前权限/flag/预算/deadline预检；必要审批绑定参数hash和资源版本，由Run持久等待；批准后复核身份、撤销、参数与资源；持久调用意图再派发；结果规范化、账本对账与用量结算后反馈Agent",
 "Tool拥有调用账本与效果记录；ApprovalRef指向Run权威决定，模型不能自填approved。",
 "参数错误可修复但不执行；拒绝返回declined不能换工具绕过；timeout保持可能unknown",
 "闸门与参数校验必经，发现可跳过；只读缓存命中仍生成当次调用Item。",
 "审批等待时不提前发请求；参数修改旧批准失效；ToolResult能区分业务失败与基础设施失败")
add("tool.effects", "action_id: ID; business_key: str?; normalized_arguments_hash: Hash; provider_ref: Ref; attempt_id: ID",
 "执行前持久保存pending意图与稳定业务键；适配器发送并保存真实请求/回应引用；confirmed仅在提供方状态足够明确时记录；网络中断/崩溃结果未知标unknown；恢复用业务键/请求ID查询实际状态；确定未发生且契约允许后才能重试",
 "动作与attempt分开，重试不换逻辑action/business key；外部幂等仍需提供方支持。",
 "无法查询保持unknown且阻止依赖成功；重复回执幂等提交；提供方不支持对账需用户/人工处理",
 "幂等账本不能TTL当缓存淘汰；查询状态预算计入原Run。",
 "发送后崩溃不重复发布；超时不写成failed后重发；外部最终回执能更新未决状态")
add("tool.failure", "failure: ToolFailure; equivalence_contract_ref: Ref?; remaining_budget: Budget; attempts: int",
 "按参数/权限/业务/基础设施/限流/unknown分类；权限拒绝不重试绕过，参数错误交Agent修复；只读或确认幂等瞬时错误在剩余deadline内退避；熔断仅阻止故障提供方新调用；等价契约满足才切换，否则返回能力差异让Agent决定；unknown写先走效果对账",
 "每次尝试记录实际provider、等价契约版本、用量与恢复原因。",
 "最大尝试/时间达到返回retry_exhausted；非等价候选只建议；业务不满足不假装网络恢复可解决",
 "有抖动的有界退避，减少故障期间拥塞；熔断状态按提供方维护。",
 "摘要不能自动代替原论文；429有限等待；拒绝发布不能改另一发布工具绕过")
add("tool.mcp", "provider_ref: Ref; connection_revision: int; transport_config_ref: Ref; session_id: ID?",
 "读取有效账号/提供方引用，不加载凭据进模型；建立协议会话并发现能力；工具名放provider命名空间，能力schema与版本入Registry；远端调用通过统一Tool闸门与结果规范化；健康变化有限重连并更新能力revision；撤销关闭会话和失效绑定，未知写不重放",
 "Tool持有协议Session，控制层持有账号授权；连接状态不能充当动作批准。",
 "协商不支持返回protocol_mismatch；掉线写结果可能unknown；能力变更让旧绑定stale",
 "会话复用有TTL/并发/健康限制；远端大结果受控分页。",
 "不同provider同名工具不混淆；撤销后旧session不可调用；远端描述不会变系统指令")
add("tool.adapters", "provider_kind: local|runtime|mcp|api; validated_call: Ref; deadline: Timestamp",
 "按不可变ToolSpec选择适配器，不让模型指定任意服务地址；运行时控制工具进入目标Runtime公共facade；Workspace动作进入受控Runner/沙箱路径；第三方调用由受控服务凭据与数据策略适配；保留原始返回与实际效果信息交Normalizer",
 "适配器不拥有目标Runtime业务状态，只持调用/协议关联引用。",
 "不支持参数返回unsupported而非静默忽略；提供方连接错误类型化；反序列化失败保留原始受控引用",
 "协议池并发有界；适配器超时不重置Run截止。",
 "agents.create确实进入Agent Registry；process.exec不在Runtime服务器环境执行；API密钥不进入命令参数")
add("tool.results", "raw_result_ref: Ref; provider_status: str; business_status: str?; effect_state: EffectState; output_schema_ref: Ref",
 "验证输出schema和提供方语义；区分网络成功与业务成功；保存原始受控输出并计算摘要/分页索引；提供status、failure_class、retryable、evidence_refs与效果状态；按模型读取预算返回必要字段，后续Context可压缩但不得改写实际结果",
 "原始输出保留来源/版本/采集时间；摘要是派生内容，不作为唯一事实。",
 "HTTP200但业务失败仍失败；输出缺关键字段返回protocol_invalid；结果过大返回分页引用不是截断成功",
 "限制解压、解析、输出大小；读取缓存保留原采集时间并复核新鲜度。",
 "500MB输出不会塞进prompt；工具说‘通过’但无执行证据不算测试通过；分页可追溯原始结果")
add("tool.audit", "call_ref: Ref; approval_ref: Ref?; actor: Principal; effect_state: EffectState; usage: Usage",
 "从实际调用取主体、动作、版本、批准依据和时间；记录尝试/结果/效果状态及数据引用；对敏感字段脱敏并保持授权诊断入口；向Run追加必要交互/审计事件，向Observability报告诊断span；审计必需动作在落盘失败时停下",
 "关键审计不可采样丢失；Trace可按政策采样，二者用调用ID关联。",
 "普通观测故障不回滚已完成外部效果；审计必需且不可写返回audit_unavailable；缺关联标识拒绝不明调用",
 "不复制所有原始正文到日志；保留与删除遵守来源政策。",
 "重试成本不漏记；日志无凭据；未知效果仍能从审计关联到账本")

add("workspace.binding", "device_id: ID; project_root_choice: Path; requested_capabilities: set[read,write,exec]; expected_binding_revision: int?",
 "由用户选择设备/项目根并确认能力；本地Runner解析真实路径、链接和平台边界；服务端保存设备/根/范围绑定，Runner保存本地授权；每次操作同时核对绑定/授权与实际解析路径；断开/撤销停止新动作并告知未决进程",
 "绝对路径是受控元数据；服务端scope不能替代Runner真实授权。",
 "路径越界拒绝；设备不匹配返回binding_mismatch；链接逃逸拒绝；Runner断开不可伪装读取成功",
 "只缓存绑定元数据，写/exec当前复核；敏感本地路径不送普通诊断正文。",
 "输入C盘路径不会获全盘访问；符号链接越界被阻止；切设备旧句柄无效")
add("workspace.base", "base_kind: commit|working_tree|artifact; source_ref: Ref; include_rules: IncludeRules; expected_source_revision: Version",
 "按用户选择读取提交或当前目录；纳入已授权的未提交修改与未跟踪文件，排除凭据/缓存规则；复制时校验文件前后hash检测变化；生成文件清单、规则版本与基础来源；稳定后发布BaseStateSpec供隔离实例",
 "基础快照不可变；不改变用户源目录或提交用户改动。",
 "复制中源变化返回snapshot_unstable并有限重试；无权文件不偷偷纳入；快照空间不足明确失败",
 "基于内容hash复用不可变块；复制额度与磁盘上限由环境策略约束。",
 "未提交修改进入正确输入；复制中修改不会产生混合快照；非Git项目可版本化")
add("workspace.isolation", "base_state_ref: Ref; mode: isolated_copy|worktree|native|cloud; writer_agent_ref: Ref",
 "按任务所需与实际后端能力选择工作副本；并行写实例分配独立目录/分支，只读共享稳定基础；native模式明确实际权限并限制同目标并发写；记录隔离类型/根/基础revision；释放前保存产物和未处理改动，按租约停止进程",
 "WorkspaceHandle绑定Run/Agent与基础版本；分支合并不自动发布外部动作。",
 "不支持的隔离模式返回unsupported；目录分配失败不标ready；存在未处理改动禁止直接删除",
 "只读无需复制可写分支；CPU/磁盘/TTL由环境策略控制。",
 "兄弟写互不覆盖；venv不标OS沙箱；回收后已交付产物仍可读取")
add("workspace.environment", "workspace_ref: Ref; template_ref: Ref?; dependency_requirements: list[Requirement]; initialization_policy: Ref",
 "先检测本地项目现有工具链与依赖；满足要求直接记录实际版本；不足时在授权项目环境安装，系统级安装另申请范围；初始化动作同样通过Tool策略；健康检查后ready，失败保留日志；终止/回收遵守用户保留服务与产物策略",
 "EnvironmentManifest记录模板、工具链、锁文件、平台、实际隔离和ready证据。",
 "安装失败标preparation_failed；网络/系统权限不足返回范围缺口；不能用空目录冒充可测试环境",
 "平台基础模板可预装通用语言，项目依赖隔离；安装缓存校验来源/版本。",
 "Go项目优先现有Go版本；不会在Runtime服务venv装任务依赖；健康失败不执行测试")
add("workspace.process", "workspace_ref: Ref; executable: str; argv: list[str]; shell: str?; cwd_ref: Ref; timeout: Duration",
 "确认工作区/当前范围与实际隔离；优先executable+argv，显式shell视更宽执行能力；采集受控目录执行前状态并创建process lease；在Runner或沙箱执行，流式日志受限并保存结果；结束/取消后采集实际改动与退出状态，保留后台服务明确租约",
 "ProcessRecord关联真实环境、命令、PID/lease、退出码、日志与ChangeSet；不是模型自报测试。",
 "超时发送停止并核对状态；无法停止返回still_running；shell写出授权范围由实际隔离强制",
 "并发/输出/CPU/内存限额；poll有cursor和有界等待，不忙轮询。",
 "go test记录真实退出码；shell创建文件也进入diff；取消后仍在运行明确展示")
add("workspace.changes", "base_revision: Version; target_revision: Version; selected_unit_ids: list[ID]?; expected_current_revision: Version",
 "比较基础/目标形成稳定ChangeUnit和依赖；提交时核对当前用户目录是否改变；不同文件可合并，同文件三方比较，语义/二进制冲突显式返回；局部接受检查单位依赖并重验实际合并版本；撤销生成逆向ChangeSet而非覆盖旧整目录",
 "CAS提交新的workspace revision；保留原变更/反向变更和用户审阅来源。",
 "用户后续修改返回conflict；格式不支持块级返回unsupported_granularity；过期验证报告失效",
 "按变更依赖重验，避免无关文件全项目重跑；hash省略未变块比较。",
 "撤销保留用户新增编辑；部分接受不能打断依赖；旧base不能静默覆盖当前文件")
add("workspace.artifacts", "workspace_ref: Ref; content_ref: Ref; format_kind: str; provenance_refs: list[Ref]; version_policy: str",
 "核验实际内容存在、类型、可访问与来源版本；通过格式adapter提取预览与可编辑能力；登记不可变ArtifactVersion和来源/验证引用；导出生成授权下载引用；外部公开发布必须另有Tool动作，不与登记混同",
 "产物本体是权威对象不按缓存TTL淘汰；预览派生内容可重建。",
 "文件缺失返回artifact_missing；格式不支持保留原件与下载；解析失败不宣告质量通过",
 "大文件流式保存/预览分页，用户私密内容不暴露公开URL。",
 "注册文件不等于发布网站；预览失败仍能安全下载原件；成果删除会让引用明确gone")
add("workspace.review", "review_set_ref: Ref; selected_units: list[ID]; decision: accept|reject|revise; position_anchor: Location?",
 "固定基础/目标revision供预览diff；用户按文件/块/结构单元选择并校验格式能力；提交前复核当前revision与改动依赖；接受后生成实际新版本及所需重验，不改旧报告；位置反馈绑定artifact version并形成新的用户输入",
 "Workspace记录Delivery审阅状态，Run记录用户动作；AI完成与用户接受独立。",
 "过期位置先重新定位或返回stale；局部冲突保持待解决；格式无块能力明确整版接受",
 "只请求所选改动预览；不把所有二进制文件转巨量文本diff。",
 "用户反馈准确定位该版本；AI不能自行accept；局部接受后的测试绑定新版本")

add("model.catalog", "visible_scope: Scope; required_capabilities: set[str]; catalog_revision: int?",
 "读取管理员启用模型元数据；按用户可见域、提供方状态与能力筛选；精确名称和已登记别名解析到canonical ID，模糊相似名称仅候选；返回实际版本/可用状态与限制；调用时仍重查下线/撤销",
 "平台配置是目录来源，Model保存解析与调用实际目录revision。",
 "精确缺失返回model_not_found；别名多解返回ambiguous；故障目录返回unavailable不猜模型",
 "目录摘要可缓存，作用域与revision进key；按需查询不常驻所有型号。",
 "猜测型号不会创建；无权型号不出候选；下线后缓存目录不允许新调用")
add("model.policy", "conversation_selection: ModelSelection; parent_policy_ref: Ref?; explicit_child_request: ModelRequest?; user_source_ref: Ref",
 "根实例解析用户选定固定模型或Auto；子实例默认继承父政策，用户明确指定才覆盖；核对指定来源而非只相信模型提交的source_ref；定义inherit保留继承意图，启动时解析实际父模型；会话模型改变默认下次Run生效，当前Run须明确修订",
 "ResolvedModelPolicy绑定用户来源、实际版本与路由范围，Run保存引用。",
 "无来源覆盖拒绝；不存在子模型反馈当前主LLM且不改inherit；Auto无候选返回缺口",
 "角色候选只做固定模式兼容检查；预览/规划/审查也继承同政策。",
 "根A→未指定子A→孙A；明确子B→其孙B；LLM不能自行给worker选廉价模型")
add("model.capability", "policy_ref: Ref; requirements: CapabilityRequirements; context_tokens: int; budget_ref: Ref",
 "检查固定模型是否支持必要工具/结构/输入类型与窗口；固定不兼容返回具体能力缺口；只有Auto授权范围内过滤候选；依据真实任务质量/延迟/成本选择已评测兼容模型；输出实际配置与版本，不能静默删除必要参数",
 "记录选择理由与候选策略版本，不变更用户授权范围。",
 "能力缺失返回capability_mismatch；上下文超限返回context_overflow；固定模式故障仅允许同模型重试",
 "参考实际完整任务费用而非只看单次输入价格；兼容元数据可复用。",
 "无tool calling模型不会冒充支持；明确模型不可用不换型号；Auto不超出许可列表")
add("model.gateway", "context_snapshot_ref: Ref; model_config: ResolvedModelConfig; output_protocol: Protocol; attempt_id: ID",
 "复核当前模型/提供方有效状态；向Run预留调用预算并服从剩余deadline；用服务端凭据选择adapter，规范请求；绑定流式attempt并验证动作输出；成功或失败都记录实际用量/费用，释放未用预留；类型化错误交Recovery",
 "保存调用ID、模型/参数/输入引用与attempt，密钥不保存于prompt/log。",
 "配额不足不发送；协议不支持明确unsupported；传输取消不假装供应商未计费",
 "按provider限流/排队有界；稳定前缀缓存只通过供应商支持接口。",
 "流重试能区分两个attempt；provider错误能追溯；未经支持参数不被悄悄忽略")
add("model.adapters", "provider_ref: Ref; resolved_model_id: ID; messages: list[Message]; tools: list[Schema]; reasoning_config: Object?",
 "按adapter能力声明转消息/工具schema；检查具体模型支持的推理/结构参数；解析流式增量、工具参数与最终usage；保留供应商实际model/version和缓存用量；规范错误码但同时保留可诊断原始受控引用",
 "adapter协议版本固定，供应商响应标识用于对账；不伪造统一能力。",
 "字段不支持返回unsupported；流截断标incomplete；usage缺失标pending_usage不估成零",
 "接口契约测试用受控fixture；KV缓存内部不可假设可读取/可迁移。",
 "错误工具JSON不直接执行；缺usage后续可核对；不同provider同名参数不当同义")
add("model.recovery", "failure: ModelFailure; previous_attempt_ref: Ref; remaining_budget: Budget; retry_policy_ref: Ref",
 "分类限流/网络/协议/参数/取消错误；同固定模型的瞬时失败有限退避；Auto仅在许可兼容候选内切换；中途流失败新attempt从确定边界重启，不将两次delta拼接；记录全部失败费用并按重复无进展停止",
 "新attempt与同一逻辑生成关联；旧输出保留诊断但不能成为有效动作提案。",
 "参数错误回Agent/Context修复；固定模型持续失败明确说明；取消不自动重试",
 "传递剩余deadline，退避不能重新取得全预算；切换配置公开记录。",
 "同一工具提案不因重试被执行两次；用户固定A无暗换B；失败成本纳入总额")
add("model.usage", "call_ref: Ref; provider_usage: Usage?; reserved_budget_ref: Ref; actual_config_ref: Ref",
 "核对attempt和供应商响应标识去重usage；区分输入/输出/推理/缓存字段的实际计费口径；结算预留与实际费用，未知费用留待核对；回传预算警告与诊断指标；记录实际模型版本而非用户显示名称",
 "Model拥有调用记录，Run Budget Ledger是预算余额权威；重复回执不能二次扣账。",
 "usage缺失返回pending；超出预留立即限制后续动作并报告；金额口径未知不伪造价格",
 "账单聚合按运行/角色/attempt，缓存节省以真实提供方用量为依据。",
 "失败重试全部计费可见；缓存命中仍计当前输出；接受成果成本含未接受尝试")

add("run.history", "conversation_id: ID; turn_id: ID; input_content_ref: Ref; source: user; dedupe_key: str",
 "验证消息归属并追加不可变Turn；原文、附件引用、显式用户配置一起登记；steer/审批答复以新输入和关联Item记录，不改过去原文；按授权读取顺序和版本；删除按保留政策标不可再读取并传播派生依赖",
 "History为用户原文权威；云/本地存储权威选择独立于本地执行位置，适配器接口一致。",
 "重复Turn幂等返回；越权会话拒绝；缺失历史显式返回，不能拼凑猜测原文",
 "客户端缓存仅供显示/草稿；压缩模型prompt不删除用户历史。",
 "预览不会变用户指令；删除资料不能从旧Run恢复；重发输入不重复历史")
add("run.state", "run_id: ID; expected_revision: int; transition: Transition; item_patch: ItemPatch?; completion_proposal_ref: Ref?",
 "校验请求主体/版本与允许转换；领域动作实际确认后写对应Item；running/verifying/waiting等并非必经；完成时核验提案、必需检查、未决效果和成果revision；分别提交completed状态及succeeded/partial/blocked等outcome；Delivery用户接受另由Workspace记录",
 "本地RunState+关键Event事务提交；外部效果通过Tool账本关联不假定分布式原子。",
 "非法转换拒绝；旧版本返回stale；缺证据不succeeded；终态不抹去独立未决效果",
 "最小轻量Run不物化DAG/TaskBoard；未知Item可通用传输。",
 "模型finish不会直接success；部分交付不会装完整；终态保留未决状态入口")
add("run.events", "stream_id: ID; event_id: ID; base_revision: int?; stream_seq: int?; payload_ref: Ref; cursor: Cursor?",
 "追加关键事件并分配单调序号；增量绑定Item/base/new revision；订阅按cursor续接并按event_id去重；缺序号/历史被裁剪返回快照+新cursor；replay只重建状态和UI，不发起工具调用",
 "关键事件不可因Trace采样而丢失；保留/快照压缩策略保持可恢复边界。",
 "未知类型通用显示；cursor过期返回snapshot_required；事务失败不能提前播成功事件",
 "流传输背压有界；高频临时进度可合并，关键完成/审批不可丢。",
 "重复delta不重复内容；断线审批仍可定位；回放不重复安装/发布")
add("run.budget", "reservation_id: ID; parent_run_id: ID; estimates: ResourceVector; deadline: Timestamp; expected_ledger_revision: int",
 "准入核对活跃Run与总额；按模型/工具/子实例/评审预留资源向量；子额度来自父额度不另造余额；执行实际用量结算并释放剩余，unknown待核对；超额/到期停止新调度，允许明确用户预算修订；队列满返回受控等待/拒绝",
 "账本预留/结算幂等且CAS/事务保护；时间策略记录审批等待如何计入。",
 "额度不足返回budget_exceeded；重复结算不二次扣；未知计费保留责任项",
 "并发不等于各自独立最大预算；各层传递剩余deadline，不能续满时限。",
 "两个同时reserve不会超售；失败调用费用计入；父取消释放未用子预留")
add("run.approval", "action_id: ID; arguments_hash: Hash; resource_revision: Version; mode: assisted|manual|automatic; control_mode: steer|enqueue|replace|cancel|deliver_partial?",
 "审批绑定主体、动作/参数、资源、期限和政策；manual等用户，assisted只在预授权范围由独立Reviewer决定，automatic不提示但仍受范围约束；明确决定持久化并唤醒相关节点；执行前由Tool/Runner复核当前撤销与变化；steer等控制回执注明生效安全边界和不能取消动作",
 "Run审批是权威，Reviewer不能审批自己，拒绝记录不可被换工具绕过。",
 "无回复/超时不批准；参数变化返回approval_stale；代审不确定升级用户；控制版本冲突返回现态",
 "只暂停受影响节点；合并相关用户问题，不能为了减少提示扩大授权。",
 "拒绝不执行；批准后目标文件变化重新判断；代审模型继承用户选择")
add("run.checkpoint", "committed_event_seq: int; domain_refs: dict[str,Ref]; pending_call_cursor: Cursor; schema_version: Version",
 "在可恢复安全边界收集已提交领域版本；保存计划/实例/上下文/工作区/预算引用与Tool账本游标；检查关键引用可解析，标明未决效果；原子发布本地checkpoint指针与事件序号；不序列化连接、密钥或隐含思维为恢复权威",
 "引用各领域权威状态，不复制可独立改写的第二套计划/审批；失败保留上个有效点。",
 "部分引用未提交不发布；损坏checkpoint回上个点并对账；外部状态不能凭快照声明原子",
 "阶段增量checkpoint，频率由恢复代价与写入成本决定。",
 "崩溃恢复能定位未决调用；checkpoint不含服务密钥；两次快照不混领域revision")
add("run.resume", "checkpoint_ref: Ref; expected_run_revision: int; requester: Principal; recovery_mode: replay|resume|rerun",
 "先取得运行租约；检查业务schema/定义/技能/环境兼容，必要迁移显式记录；重建连接并核验当前撤销；通过Tool对账pending/unknown效果；Workspace核对真实文件与环境变化；恢复无未决依赖的节点，或返回冲突/受阻；rerun建立新Run，不将其伪装为历史回放",
 "Resume不接管各领域写入；恢复事件关联旧checkpoint与当前版本。",
 "不兼容返回migration_required；未决结果无法核实保持blocked依赖；双领返回lease_conflict",
 "先恢复必要资源，回放只读日志；恢复后重试仍使用原逻辑动作键。",
 "旧批准撤销后无法恢复执行；原项目改动能发现；恢复不重复外部写")
add("run.cancel", "target_run_ref: Ref; target_agent_refs: list[Ref]?; reason: str; preserve_artifact_refs: list[Ref]",
 "先持久取消请求并停止新节点调度；递归通知子Agent、Tool调用和Workspace进程；有界等待可取消执行器确认，再按能力强停；不能取消的外部动作继续独立对账；保留已确认产物并返回实际停止/仍在执行/unknown列表",
 "cancel_requested与执行器实际取消分别记录，cancelled不能掩盖外部未决效果。",
 "已终止请求幂等返回；停止进程失败标still_running；缺权限不能取消别的会话Run",
 "清理未用预留与租约；已计费用不因取消回退为零。",
 "父取消影响子；前端不提前显示全部停止；保留成果可下一Run引用")
add("run.trigger", "trigger_spec_ref: Ref; occurrence_key: str; target_task_ref: Ref; overlap_policy: queue|skip|parallel",
 "只消费已被用户授权的TriggerSpec；按时区/来源生成稳定触发occurrence键；当前授权/预算再次校验；重叠按queue/skip/parallel明确处理；创建或唤醒指定Run并按 meaningful变化通知；首版预留不默认提供定时能力",
 "每次触发与授权版本留记录，节点Scheduler不负责决定定时唤醒。",
 "重复触发幂等返回；目标已撤销不启动；配额不足按策略记录skip或等待",
 "通知抑制无变化，不用频繁轮询制造状态消息。",
 "时区与夏令策略明确；重复事件只建一次Run；定时不增加工具权限")

add("support.configuration", "configuration_patch: Object; expected_revision: int; credential_ref: Ref?; account_consent_ref: Ref?",
 "管理员发布模型/搜索/提供方/环境/政策配置；私人账号连接由用户明确授权，配置身份与执行身份分开；校验引用与配置兼容后生成不可变snapshot；Runtime固定常规版本并实时核验撤销/限额；失效通知目录、绑定与缓存",
 "凭据存在受控CredentialStore，普通配置仅引用；管理API不进入Agent工具目录。",
 "无管理员权限拒绝平台改动；账号撤销立即禁调用；过期配置CAS冲突返回现态",
 "首期API/CLI，管理UI后置；平台服务密钥不发本地任意代码。",
 "终端用户不必配搜索key；Agent不能启用隐藏提供方；私人连接仍需用户授权")
add("support.extensions", "bundle_ref: Ref; content_hash: Hash; dependency_manifest: Manifest; requested_state: install|activate|revoke|rollback",
 "校验包完整性、来源与必需能力；登记不可变版本和权限请求，安装不自动授权；候选版本跑受影响契约与真实任务回归；通过ReleaseGate才允许新激活；回滚指向旧内容，撤销阻止尚未执行动作并失效派生绑定",
 "ReleaseManifest绑定技能/工具schema/prompt/adapter/索引配置，运行实际版本固定。",
 "同版本不同内容拒绝；依赖不满足不激活；恢复旧Run不兼容需迁移或受阻",
 "按受影响依赖回归，不先造完整插件市场。",
 "升级可追溯旧包；撤销比固定版本优先；恶意包无法取得系统权限")
add("support.cache", "namespace: str; dependency_refs: list[Ref]; canonical_parameters: Object; scope: Scope; freshness: FreshnessPolicy",
 "领域先声明可复用性/有效性；按真实输入/版本/权限域生成键并二次核验命中；miss按key合并允许的在途读取，组内再查缓存；等待者各自deadline/取消，最后等待者退出按执行器能力回收；写入带依赖/来源时间，撤销/删除传播失效；记录实际有效命中与净节省",
 "缓存可丢失重建；不储存唯一审批、账本、历史或产物。",
 "刷新失败释放等待者；授权变化不能返回旧私密结果；写动作拒绝结果缓存/在途去重",
 "层次按实际部署需求，抖动TTL/配额防热点；不为了命中错报时间或工具范围。",
 "单等待者取消不杀他人读取；失效旧摘要不可用；缓存故障不破坏权威状态")
add("support.observability", "trace_id: ID; span_id: ID; parent_span_id: ID?; attempt_id: ID?; domain_revision_refs: list[Ref]; metric: Object?",
 "各facade发开始/结束span，包含实际版本/关联调用和错误；用来源引用记录诊断而非完整私密正文；脱敏和访问策略后写Trace/Metrics；排队/重试/缓存/用户等待分别测量；提供按Run与调用定位故障；授权失败样本送离线评测，不自动把日志当记忆",
 "Trace是诊断派生记录，Run事件/审计权威不被采样替代。",
 "普通Trace失败记录降级；必须审计动作服从其阻断政策；无法关联标异常不合并别的Run",
 "高频诊断可采样但标策略，隐藏思维/凭据不保存；尾延迟分解而非只平均。",
 "能定位版本与失败尝试；日志无key；清理来源后按保留政策清理诊断派生正文")
add("support.evaluation", "candidate_manifest: Ref; baseline_manifest: Ref; dataset_version: Ref; fixture_environment: Ref; grader_config: Ref",
 "固定真实输入、初态、权限与工具fixture；开发/回归/隐藏集分开并查近重复；隔离跑新旧版本，外部写禁用或模拟；先真实状态与硬约束，再事实/语义评分和人工校准；按办公/开发/学术与失败类型报告接受、返工、全成本/延迟；用证据决定发布门槛，不只看总分",
 "评测输入、评分器和报告版本不可变；一次运行验收不替代离线系统比较。",
 "零接受数成本比不可计算；裁判不确定抽检；被评输出不能改变裁判指令；不完整fixture标不可比",
 "同预算比较单/多Agent；错误样本授权脱敏后回归，禁止真实重复发布。",
 "新prompt退步被发现；同模型自评误差人工校准；不能隐藏失败重试成本")
add("support.stores", "repository_kind: history|object|index|cache|trace; scope: Scope; key: ID; expected_version: Version?",
 "每领域通过自己的Repository接口读写；共享设施提供事务/CAS、对象引用、索引发布与缓存能力适配；资源读写检查归属和保留政策；备份恢复重放删除/撤销记录；迁移版本显式校验，不让万能JSON状态表承担所有领域规则",
 "物理数据库可共用，逻辑写入所有权不同；可重建派生与权威数据采用不同保留规则。",
 "版本冲突类型化；部分对象上传保留pending并清理未引用块；迁移失败不宣布ready",
 "索引/缓存可失效重建，权威历史与账本不按LRU淘汰。",
 "旧备份不恢复被忘记记忆；CAS不能双成功；丢缓存仍能继续查看交付成果")

add("tool.invocation.schema", "tool_version: Version; arguments: Object; supplied_context: Object?",
 "载入精确工具版本schema；执行schema允许的参数规范化，不自行改变语义；验证资源引用类型并定位实际版本；忽略或拒绝模型提供的主体/批准字段，用可信上下文替换",
 "保存规范参数hash和工具版本供审批绑定。", "结构不合法返回invalid_arguments；资源不可定位返回reference_error",
 "schema按不可变版本复用，不缓存权限结论。", "同语义允许规范化保持稳定hash；伪造approved无法通过")
add("tool.invocation.precheck", "validated_call_ref: Ref; effective_policy_ref: Ref; budget_estimate: ResourceVector",
 "按当前主体/资源检查flag与能力；按实际副作用类别判断风险，不看工具名字猜只读；检查剩余deadline和预算；返回允许/需审批/拒绝，尚不执行",
 "PrecheckDecision短时记录不是永久授权。", "policy_denied不能替换工具绕过；budget_exceeded返回资源缺口",
 "并行读取元数据可以，动作必须等待强制检查完成。", "只读名称但写副作用受写权限约束；检查未完成不会派发")
add("tool.invocation.approval", "action_ref: Ref; arguments_hash: Hash; resource_revision: Version; expires_at: Timestamp",
 "向Run提交绑定动作的ApprovalRequest；只暂停该动作依赖，其他独立读取可继续；等待用户或独立代审的明确回执；批准返回ApprovalRef给执行前复核，拒绝交主Agent",
 "Run为审批权威，此节点不自批。", "无响应返回waiting不是approved；过期返回expired",
 "有限等待/事件唤醒；不用轮询模型反复问相同问题。", "重连后审批可恢复；拒绝后没有外部调用")
add("tool.invocation.recheck", "call_ref: Ref; approval_ref: Ref?; expected_resource_revision: Version",
 "重新读取当前身份与撤销；比较实际参数hash和审批绑定；核对资源版本/有效期/受限持续授权谓词；通过才签执行所需短期上下文，变化返回重新决策",
 "保存实际复核policy revision与结果。", "approval_stale重新申请或解释；当前撤销直接拒绝",
 "即使命中只读缓存也要复核当前范围。", "批准后用户换文件不会执行旧批准；模式改变不能抹掉原拒绝")
add("tool.invocation.dispatch", "validated_action_ref: Ref; reservation_ref: Ref; business_key: str?; provider_binding_ref: Ref",
 "持久登记Tool pending意图；核对目标适配器绑定和剩余deadline；执行精确版本动作并保留传输关联ID；返回实际效果信息给Normalizer，不在此层重复创建业务动作",
 "先意图后发送；attempt关联稳定action ID。", "发送后中断标unknown；适配器不可用返回typed failure",
 "提供方并发上限和队列有界。", "崩溃前有可对账意图；外部写不靠Singleflight去重")
add("tool.invocation.result", "provider_result_ref: Ref; effect_state: EffectState; attempt_usage: Usage",
 "输出schema核验并分离业务与基础设施状态；确认或保留未决效果到账本；保存原始结果并分页/摘要；结算实际用量，向Run/Agent反馈类型结果",
 "结果提交和账本进展保持可恢复关联，终态仅由Run提交。", "缺业务状态不能猜成功；超大结果返回raw_ref与分页",
 "失败尝试用量同样结算。", "HTTP200业务失败仍失败；未决不变成确认完成")

add("agent.collaboration.contract", "parent_goal_ref: Ref; proposed_goal: str; input_refs: list[Ref]; output_contract: Contract; budget: Budget",
 "说明可独立验收子成果与父目标关系；核对必要输入是否已经可读、依赖是否满足；计算父权限/角色/产品/委托限制交集；将协调/汇总预算算入总额，收益不足保持单Agent",
 "DelegationSpec固定task/plan与输入版本。", "子目标模糊返回contract_gap；额外预算不足不创建实例",
 "一次工具操作一般直接工具执行。", "节点与Agent不是一一对应；单Agent基线仍可选择")
add("agent.collaboration.instance", "definition_ref: Ref; delegation_ref: Ref; parent_agent_ref: Ref; creation_key: str",
 "工厂校验定义enabled及精确版本；解析继承模型与角色权限交集；预留子预算并分配私有上下文，写任务需要隔离工作区；持久实例关联后调度，反馈丢失按creation_key查询",
 "实例状态与定义分开，复用定义不复用scratch。", "定义停用拒绝新实例；模型无效返回主LLM；预留失败回收分配意图",
 "只读共享快照不复制可写目录。", "同定义两个实例互不污染；重复invoke不启动第二实例")
add("agent.collaboration.channel", "message_id: ID; from_ref: Ref; to_ref: Ref; payload_refs: list[Ref]; task_revision: int",
 "核对同任务关系和收发权限；消息注明目标/引用/期待回复/deadline；关键分配/结果消息持久去重，临时进度按策略保留；接收者按自己scope重新解析引用，控制互聊深度与次数",
 "消息记录归Agent，Run事件仅引用；不共享完整prompt。", "过期目标返回stale_message；无权引用不送达正文",
 "摘要与raw_ref组合，按需要读取原数据。", "兄弟看不到私有scratch；重复message ID只消费一次")
add("agent.collaboration.join", "required_result_refs: list[Ref]; expected_task_revision: int; reducer_spec: Ref",
 "检查每项必需结果状态与实际版本；按输出契约读取证据/产物并区分候选与确认；冲突结论保留差异，必要查证后整合；CAS提交共享板并回父Agent，缺口保留不伪造汇总成功",
 "整合结果绑定全部输入依赖。", "必需子failed不能Join成功；旧结果返回stale；矛盾未解标partial",
 "按需读取证据，不复制全部子历史。", "新用户约束后旧汇总不可接受；三个子成功一个必需失败不宣告完成")
add("agent.collaboration.handoff", "from_agent_ref: Ref; to_agent_ref: Ref; expected_control_revision: int; unfinished_refs: list[Ref]",
 "验证目标有完整后续职责和许可模型/权限；核对在途与未决动作的归属/对账方案；准备最小交接上下文与回转条件；CAS更新ConversationControlLease并发送交接事件；旧控制者之后的过期动作/回复被拒绝",
 "Agent拥有唯一ControlLease，Run保存恢复引用。", "CAS失败保留现持有者；循环/次数超限拒绝；敏感未决无法处理时等待",
 "不默认开启，局部信息查询使用delegate。", "不会两个主Agent同时最终回复；移交不复制全部授权")
add("agent.collaboration.cancel", "agent_tree_ref: Ref; cancel_reason: str; pending_call_refs: list[Ref]",
 "接收Run取消并停止此子树新委派；按父子关联通知活动实例；请求Tool/Workspace执行器真正停止并收回未用预留；未决效果留对账，已确认结果保留来源状态",
 "实例取消回执归Agent，Run聚合生命周期。", "执行器不可取消返回pending_effect；过期回执不能恢复新实例",
 "取消传播有界并去重通知。", "子又委派孙时都收到取消；费用不因取消归零")

add("agent.completion.contract", "user_input_refs: list[Ref]; task_frame_ref: Ref; proposed_requirements: list[Requirement]",
 "提取原文和用户纠正的必需目标；分开硬约束与开放质量标准；LLM可提出补充验证但不能删必需要求；为每项确定可接受成果/证据或明确待澄清",
 "DeliveryContract追加版本并绑定用户/政策来源。", "关键标准冲突返回clarification_required；模型自降目标拒绝",
 "简单回答使用轻量契约，不造代码测试项。", "办公/学术/开发不是同一固定字段；用户未要求部署不额外强制部署")
add("agent.completion.evidence", "contract_ref: Ref; artifact_refs: list[Ref]; coverage_gaps: list[ID]",
 "按缺口选择真实读取/测试/计算/格式检查；通过Tool请求获准检查与预算；登记实际受测版本、环境和输出；把passed/failed/not_run/blocked分别返回语义核验",
 "验证证据是不可变引用，不以模型口述替代。", "环境不足标blocked；未跑标not_run；工具失败不写passed",
 "按变更依赖选择检查，不无故全量重跑。", "go test退出码可追溯；网页证据实际取得而非URL猜测")
add("agent.completion.semantic", "contract_ref: Ref; evidence_refs: list[Ref]; artifact_refs: list[Ref]; reviewer_policy: Ref",
 "让当前模型对照每项目标与证据；区分支持/反驳/未覆盖并列依据；缺口可触发获准补查或修订；必要独立Reviewer使用隔离上下文且继承模型政策",
 "VerificationReport记录判别方法版本与限制，不直接结束Run。", "缺证据保持unknown；裁判受注入指令当数据；高不确定需人工反馈",
 "无需每次独立Reviewer，不把更长推理当真实证据。", "同模型共同盲点由测试/抽检弥补；文风好不能抵消关键失败")
add("agent.completion.version", "report_ref: Ref; expected_artifact_versions: dict[ID,Version]; pending_effect_refs: list[Ref]",
 "读取真实成果/环境/目标版本；按报告依赖比较实际受测输入；核对必需检查、权限和未决效果；通过才给可提交提案，stale项计算重验范围",
 "提案绑定当前revision，最终CAS归Run。", "版本改变返回stale_verification；必需未知效果阻止succeeded",
 "不因无关文件改动一律废全报告，按依赖核对。", "局部接受后校验实际新版本；旧测试报告不能覆盖新代码")
add("agent.completion.delivery", "proposal_ref: Ref; expected_run_revision: int; artifact_manifest_ref: Ref; proposed_outcome: Outcome",
 "Run核对提案来源与版本；Workspace确保真实成果可访问；CAS写Run终态和相应交付引用；发送完整/部分/受阻说明与验证范围，用户审阅状态另存",
 "终态与必要事件本地事务提交；外部公开发布另走Tool。", "CAS冲突重读而非覆盖；产物不可读不能假交付；未决项保持可见",
 "交付引用可复用，不重生成已确认产物。", "completed/partial准确显示；注册产物不会自动发邮件或发布")
add("agent.completion.acceptance", "review_set_ref: Ref; decision: DeliveryDecision; feedback_ref: Ref?; expected_artifact_version: Version",
 "通过Workspace审阅固定成果；用户接受/拒绝/局部接受分别记录；位置反馈成为新用户输入；需要修改时基于当前版本重新建立契约与Run，保留未受影响成果",
 "用户接受的权威由Workspace保存，模型无权替用户填写。", "旧ReviewSet返回stale；依赖破坏要求补验；全盘不支持时明确整版操作",
 "重复任务保留用户已改内容，不无条件重新生成整份。", "AI说满意不等于用户accepted；评论绑定具体版本")

add("context.memory.candidate", "source_refs: list[Ref]; candidate_kind: explicit|inferred; content: MemoryContent",
 "识别用户明确记住请求并保留来源；普通对话/研究结果只提炼有用途的候选；区分偏好、事实、经历与方法；推断候选不能先对用户宣告记住",
 "候选未通过之前不进入正式长期召回。", "无来源拒绝持久记忆；低稳定内容留任务范围",
 "后台推断有队列配额，不每句都抽取。", "‘记住新地址’及时确认保存状态；论文猜测不会当用户事实")
add("context.memory.policy", "memory_policy_ref: Ref; candidate_ref: Ref; target_scope: Scope; retention: Duration?",
 "检查读/贡献开关与用户要求；核对内容敏感范围、用途与保留；确定仅任务/会话/用户范围；拒绝或返回允许的写入范围给冲突检查",
 "政策版本记录，不把候选文字当授权。", "关闭贡献不写；共享范围无权拒绝",
 "只处理必要候选，不强制长期存储。", "关闭记忆仍能完成当次任务；私人内容不自动共享")
add("context.memory.conflict", "candidate_ref: Ref; existing_refs: list[Ref]; slot_key: str?; expected_revision: int",
 "先按精确槽位和有效条件查重；再用语义寻找可能冲突；用户明确纠正优先并生成supersedes；不同条件都成立分开保存，无法确定保留候选待确认",
 "不原地抹掉来源历史，提交新的事实版本。", "并发纠正CAS冲突重读；相似而非相同不得合并",
 "少量槽位不用向量检索，开放经历可向量召回。", "喜欢Go与会Go不混；旧工作地址可被显式纠正")
add("context.memory.store", "validated_memory: MemoryRecord; expected_revision: int; operation: commit|recall; now: Timestamp",
 "提交scope/source/有效期/派生关系并确认事务；更新索引与缓存依赖，索引未就绪标明确状态；召回先按当前范围/有效期过滤再排名；显式记住仅事务成功后回用户",
 "Memory本体权威，embedding为派生；保存错误可查询幂等状态。", "写失败返回not_saved；撤销记录不能召回；索引失败不假称已可检索",
 "对profile精确读，按内容hash复用派生。", "反馈丢失重试不重复事实；过期条目不影响当前回答")
add("context.memory.forget", "selector: MemorySelector; deletion_id: ID; derived_dependency_refs: list[Ref]",
 "先标不可召回并检查当前读取；沿derived_from清理摘要/索引/缓存；按保留政策处理物理副本与备份删除标记；返回完成、待清理、失败项并可幂等重试",
 "删除记录不能被旧checkpoint/备份恢复覆盖。", "部分存储失败明确pending_cleanup；无权selector拒绝",
 "批量依赖失效，物理清理后台有界但逻辑立即不可用。", "删偏好后摘要不再提它；恢复备份重放删除")

add("tool.mcp.provider", "provider_ref: Ref; account_connection_ref: Ref; expected_config_revision: int",
 "读取当前平台启用状态和私人账号授权；校验数据范围、可用凭据引用与传输限制；固定普通配置版本，当前撤销单独检查；输出仅可连接配置给会话层",
 "不复制账号授权到账本作为永久许可。", "账号过期返回reauth_required；提供方未启用拒绝",
 "配置可短期缓存，调用仍核验撤销。", "Agent拿不到key；平台启用不等于私人账号已授权")
add("tool.mcp.session", "provider_binding_ref: Ref; protocol_profile: Ref; deadline: Timestamp; session_id: ID?",
 "按支持协议建立/协商会话；健康检查记录能力与连接状态；有限重连重新核验授权；关闭和过期回收句柄，不把连接对象放checkpoint",
 "会话记录绑定账号/config revision；凭据仅适配器读取。", "协商失败返回protocol_mismatch；掉线不重放未知写",
 "连接池与并发有界，空闲TTL策略可配置。", "断开后旧句柄失效；恢复Run可以重建连接")
add("tool.mcp.capabilities", "session_ref: Ref; remote_capabilities: list[Capability]; expected_registry_revision: int",
 "列当前能力并校验schema/大小；使用provider命名空间避免同名覆盖；规范为ToolSpec且标来源信任；版本变化发布新registry revision并失效旧发现候选",
 "能力元数据入权威Registry，向量索引只存派生描述。", "畸形schema不注册；不兼容变化返回stale_binding",
 "按变化增量索引，能力描述不整包放prompt。", "两个同名MCP工具可区分；描述无法自授管理员权限")
add("tool.mcp.invoke", "validated_call_ref: Ref; session_ref: Ref; business_key: str?; attempt_id: ID",
 "必须持统一Tool闸门准入结果；核验session与工具实际版本；发送远端调用并保存关联ID；规范协议返回与大结果引用，写unknown进入效果账本",
 "不在MCP层另批准一份动作，使用原action/attempt关联。", "远端业务错误类型化；掉线写结果unknown；schema变化需重新绑定",
 "复用健康会话、遵守provider限额。", "直接绕过Tool调用被禁止；unknown不能当未发送后重试")
add("tool.mcp.invalidate", "provider_ref: Ref; reason: revoked|expired|capability_changed|disconnected; affected_revision: int",
 "先阻止新敏感调用；关闭或标无效旧session；让Registry/Discovery/缓存绑定失效；已有在途调用按取消能力和效果对账继续跟踪",
 "撤销当前生效，普通版本固定不能绕过。", "关闭失败记录仍在处理但不开放新调用；能力变化可重新发现",
 "依赖失效不清掉必要效果账本。", "旧账号撤销立即禁用；不遗漏在途外部动作")

add("run.resume.lease", "run_id: ID; node_id: ID?; expected_revision: int; lease_ttl: Duration",
 "读取现有效lease；通过事务/CAS取得owner与递增fencing版本；执行期间有界续租；结果提交检查lease版本，失租即停止新动作",
 "lease是有限执行权，不是持久工具授权。", "已被领走返回lease_conflict；过期提交返回stale_lease",
 "单进程先实现唯一执行与崩溃恢复，多worker再加跨实例协调。", "两个恢复请求只有一个有效；旧worker回执不能覆盖新worker")
add("run.resume.versions", "checkpoint_ref: Ref; current_runtime_manifest: Ref; migration_policy: Ref",
 "逐项比较schema/定义/技能/环境与调用协议版本；兼容可继续，迁移必须有明确函数与验证；固定模型政策和审批参数不静默改写；不兼容返回受阻或新Run建议",
 "记录迁移输入/输出和实现版本，保留旧checkpoint。", "迁移失败不发布新checkpoint；模型下线按用户政策返回缺口",
 "只检查实际依赖，不因无关插件升级一律阻塞。", "旧审批不被改成新权限；恢复不会偷偷换模型")
add("run.resume.access", "domain_resource_refs: list[Ref]; current_principal: Principal; current_config_revision: int",
 "重新核验当前身份、项目绑定、账号与撤销；重建连接/进程查询句柄而非复用序列化连接；检查已删除来源不重新加载；返回可继续的真实访问范围",
 "checkpoint保存引用，当前授权读取原权威。", "资源撤销返回denied；Runner断开返回disconnected；来源删除不能恢复内容",
 "优先重建必要连接，不预先启动所有提供方。", "已忘记记忆不回来；断开的本地设备不会被云目录替代")
add("run.resume.effects", "tool_ledger_cursor: Cursor; pending_action_refs: list[Ref]; deadline: Timestamp",
 "向Tool请求pending/unknown列表；用原业务键查询真实提供方状态；确认完成后记录结果，确认未发生且契约允许才重试；无法确定保留未决并阻止相关依赖",
 "Run记录对账进度引用，效果权威仍归Tool。", "provider不可查询返回unresolved_effect；回执重复幂等更新",
 "对账预算计入原任务，不拿新Run键重复外部动作。", "发信后崩溃恢复不再发；unknown不标成功或安全失败")
add("run.resume.workspace", "workspace_ref: Ref; expected_revision: Version; expected_environment_ref: Ref",
 "让Workspace/Runner检查目录、实际文件hash和环境状态；比较用户并发编辑与保存版本；冲突返回ChangeSet定位并保留用户改动；受测依赖改变让旧验证失效后再继续",
 "不将checkpoint文件镜像直接覆盖当前磁盘。", "目录丢失返回workspace_missing；环境变化要求重准备；冲突保持等待",
 "按必要文件依赖比较，无关改动不废全任务。", "用户手改文件可发现；旧go test报告不套新文件")
add("run.resume.continue", "reconciled_state_refs: list[Ref]; expected_run_revision: int; resumable_nodes: list[ID]",
 "核对租约仍有效和全部强制恢复条件；标清可继续/需等待节点；CAS提交恢复事件和当前引用；调用Agent Scheduler运行可就绪工作；既有确认成果只引用不重做",
 "恢复是继续同Run，rerun另建ID并保留关联来源。", "恢复期间用户steer导致版本冲突重读；依赖未决不调度",
 "延续原总预算与deadline，显式追加才变更。", "恢复不重做已确认写动作；重复resume不会双执行")
