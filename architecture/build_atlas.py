"""Build the design atlas and standalone explorer from one graph catalog.

This script generates documentation, not an Agent Runtime.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NODES = {}
VIEWS = {}
TYPES = {"call": "调用", "data": "数据/引用", "state": "状态/事件", "policy": "权限/配置", "lifecycle": "生命周期"}


def node(id, label, description, entry, inputs, outputs, guard, parent=None, kind="component"):
    assert id not in NODES, id
    NODES[id] = dict(id=id, label=label, description=description, entry=entry,
                     inputs=inputs, outputs=outputs, guard=guard, parent=parent,
                     kind=kind, status="设计目标，未实现 Runtime")


def edge(source, target, label, kind="call"):
    return dict(source=source, target=target, label=label, kind=kind)


def view(id, title, summary, children, edges):
    VIEWS[id] = dict(id=id, title=title, summary=summary, nodes=children,
                     edges=[edge(*e) for e in edges])
    if id in NODES:
        NODES[id]["view"] = id


node("ui", "交互页面", "用户原文、任务理解、运行过程、成果及变更审阅。", "send/control/review", "用户输入与选择", "请求与可见反馈", "任务理解是提示，原文是执行基准。", kind="boundary")
node("ingress", "产品入口", "接收请求，检查身份、资源与限额，连接事件流。", "submit/stream", "原文、附件引用、会话配置", "AgentExecutionRequest", "输入路径不自动赋予本地权限。", kind="boundary")
modules = [
    ("intent", "任务理解 · Intent", "把原文整理成带依据的目标、约束与未知项。", "understand/preview", "原文、草稿、必要资料", "TaskFrame / DraftPreview", "预览不替代用户指令；理解可以随证据修订。"),
    ("agent", "决策执行 · Agent", "组织单 Agent 循环、规划、委派、技能与完成核验。", "start/step/define_agent", "TaskFrame、能力、预算、模型政策", "动作提案、NodeResult、CompletionProposal", "LLM 提议动作，Runtime 检查权限、预算、状态。"),
    ("context", "上下文 · Context", "按目的找资料、记忆和规则，装配有来源的模型输入。", "build/ingest/remember/forget", "purpose、目标、作用域、版本、token预算", "ContextSnapshot / ContextManifest / Reference", "压缩不赋权；资料和规则按信任来源区分。"),
    ("tool", "工具执行 · Tool", "统一注册、发现、调用、审批闸门、失败治理和 MCP。", "discover/invoke/reconcile", "工具参数与可信 ToolRuntimeContext", "ToolResult、效果状态、原始结果引用", "未知写结果先核对；只有登记等价契约才自动切换。"),
    ("workspace", "工作区 · Workspace", "授权本地项目/可选云沙箱、环境、改动、产物和审阅。", "allocate/prepare/merge/review/revert", "项目授权、BaseState、操作与预期版本", "Environment、ChangeSet、Artifact、ReviewSet", "本地 Runner 再检查；cwd/venv 不等于安全隔离。"),
    ("model", "模型调用 · Model", "继承用户模型选择，适配提供方调用、恢复与用量。", "resolve_policy/generate", "固定/Auto政策、prompt、能力需求", "模型动作输出、实际版本、用量", "用户指定模型优先；不可用不能静默换模型。"),
    ("run", "运行控制 · Run", "统一生命周期、历史、事件、预算、审批、取消恢复。", "create/control/checkpoint/resume", "执行请求、版本、用户控制", "RunState、Items、事件、checkpoint", "完成文本不证明成功，completed 与 succeeded 分开。"),
    ("support", "共享支撑与控制层", "缓存、平台配置、扩展包、观测与离线评测。", "领域入口 + 共享设施", "版本配置、派生数据、诊断/评测请求", "有效配置、缓存、运行诊断、对比报告", "不成为第八个强制执行 Runtime；业务状态仍归领域。"),
]
for args in modules:
    node(*args, kind="module" if args[0] != "support" else "support")

view("overview", "UAW 总体关系", "这是职责关系图，可以有反馈与循环；不规定每个请求必经全部模块。任务依赖 DAG、Agent 委派树和工作区分支另行建模。",
     ["ui", "ingress", "intent", "agent", "context", "tool", "workspace", "model", "run", "support"], [
         ("ui", "ingress", "发送原文/干预/审阅"),
         ("ingress", "run", "创建与控制执行"),
         ("run", "intent", "发起理解或修订"),
         ("intent", "agent", "目标、约束、未知项", "data"),
         ("intent", "context", "按需补充理解材料"),
         ("intent", "model", "需要语义理解生成时"),
         ("agent", "context", "装配本轮输入"),
         ("context", "model", "需要语义压缩/摘要时"),
         ("agent", "model", "提出下一步动作"),
         ("agent", "tool", "发现/执行动作"),
         ("tool", "workspace", "受控文件/环境/进程"),
         ("tool", "agent", "定义/委派等控制工具"),
         ("tool", "context", "资料/引用等控制工具"),
         ("agent", "workspace", "隔离分配与交付协调"),
         ("workspace", "context", "授权文件与产物版本", "data"),
         ("tool", "agent", "实际结果/类型化失败", "data"),
         ("agent", "run", "预算/检查点/完成申请", "state"),
         ("tool", "run", "审批请求与用量", "state"),
         ("model", "run", "模型预算预留与结算", "state"),
         ("run", "ui", "Items、进度、审批、成果", "state"),
         ("support", "tool", "提供方与当前撤销", "policy"),
         ("support", "model", "模型目录与发布配置", "policy"),
         ("support", "agent", "技能/能力包与flag", "policy"),
         ("support", "context", "资料/记忆与保留政策", "policy"),
         ("run", "support", "关联诊断与评测输入", "data"),
     ])


def parts(parent, rows, edges, summary):
    ids = []
    for suffix, label, description, entry, inputs, outputs, guard in rows:
        id = parent + "." + suffix
        ids.append(id)
        node(id, label, description, entry, inputs, outputs, guard, parent)
    converted = []
    for e in edges:
        source, target, label, *kind = e
        converted.append((parent + "." + source, parent + "." + target, label, *(kind or ["call"])))
    view(parent, NODES[parent]["label"], summary, ids, converted)


parts("intent", [
    ("preview", "草稿理解预览", "短时只读、可取消，不阻塞发送。", "preview", "草稿 hash、最小历史", "DraftPreview", "只显示匹配当前草稿的预览。"),
    ("original", "原文读取", "读取 Run 保存的不可变用户原文。", "read_original", "original_input_ref", "原文与用户修订", "不另存可覆盖的原文账本。"),
    ("semantic", "语义解析", "分开显式目标、推断与未知；可合并进首次模型调用。", "parse", "原文与必要上下文", "目标/约束/候选解释", "不用词典判复杂度，推断不伪装用户事实。"),
    ("references", "指代解析", "定位‘这个文件’、‘上次报告’等资源。", "resolve", "表达与候选引用", "可验证资源引用", "不唯一保留歧义，不凭名称猜本地文件。"),
    ("probe", "必要信息探查", "请求 Context 或有预算的只读 Tool 补信息。", "probe", "缺口、权限、剩余预算", "证据与信息缺口", "不在理解阶段无限调研。"),
    ("ambiguity", "歧义处理", "依据后果、可逆性与证据决定开始或澄清。", "resolve_ambiguity", "候选目标与影响", "可开始/需澄清", "高影响关键条件未知时不能猜。"),
    ("frame", "任务框架", "形成版本化 TaskFrame，并保留原文引用。", "build_frame", "以上解析与证据", "TaskFrame revision", "正式理解变化说明原因，不覆盖原文。"),
], [("original", "semantic", "用户基准", "data"), ("semantic", "references", "待定位表达"),
    ("references", "probe", "按需补材料"), ("probe", "semantic", "证据反馈", "data"),
    ("semantic", "ambiguity", "候选与未知", "data"), ("ambiguity", "frame", "已定目标与保留假设", "data"),
    ("semantic", "preview", "草稿路径的短理解", "data")], "草稿与正式理解是两个入口；必要探查可循环，简单请求可以直接构建 TaskFrame。")

parts("agent", [
    ("definitions", "子Agent定义与发现", "持久会话角色的设计、创建、发现与配置版本。", "define_agent/discover_agents", "用户授权配置、角色/定义版本", "AgentDefinitionVersion / CandidateSummary", "创建角色不自动启动任务；定义修改可撤销。"),
    ("loop", "Agent 决策循环", "上下文→模型→动作→观察，主 Agent 保持精炼指令。", "step", "TaskFrame、ContextSnapshot、预算", "动作提案或答复", "失败回到决策，不强制固定业务流水线。"),
    ("assessment", "按需执行评估", "语义选择 none/steps/dag、single/parent_child、serial/parallel。", "assess_execution", "目标、能力、已知信息、成本", "ExecutionAssessment", "可合并理解，不要求独立判断 Agent。"),
    ("planning", "规划与依赖校验", "生成步骤或任务 DAG，校验每次 PlanPatch。", "plan/validate", "目标、依赖、预算、资源", "TaskGraph revision", "只有执行依赖图必须无环；计划版本之间可以迭代。"),
    ("scheduler", "节点与资源调度", "依赖满足、权限与资源允许才开始节点。", "schedule", "可运行节点、资源预留", "受控执行与 Join 条件", "节点不必须对应 Agent，能并行不等于值得并行。"),
    ("collaboration", "委派与控制权", "管理父子 Agent、消息、结果整合与可选交接。", "delegate/join/handoff", "子目标、契约、引用、权限/预算", "NodeResult / ControlLease", "子上下文独立；默认父 Agent 负责最终回复。"),
    ("skills", "技能与任务模板", "按需发现和加载方法/依赖/验收标准。", "resolve_skill/activate_skill", "目标与可见技能元数据", "固定 SkillBundle / TaskTemplate", "技能不能扩大权限，不把所有方法塞进常驻 prompt。"),
    ("completion", "完成核验协调", "按语义目标与实际证据发现缺口并提出完成。", "verify/propose_completion", "契约、成果版本、检查证据", "VerificationReport / Proposal", "真实测试、语义满足、用户接受分别记录。"),
    ("board", "共享任务板", "存目标、计划、节点结果与证据引用。", "read/commit(expected_revision)", "各节点结构化结果", "TaskBoard revision", "CAS 提交；依赖变更只使相关节点 stale。"),
], [("definitions", "loop", "固定定义实例", "lifecycle"), ("skills", "loop", "按需方法", "data"),
    ("loop", "assessment", "不确定执行方式时"), ("assessment", "planning", "需要 steps/DAG 时"),
    ("planning", "scheduler", "已校验依赖", "data"), ("scheduler", "collaboration", "需要委派时"),
    ("collaboration", "board", "提交版本化结果", "state"), ("board", "scheduler", "依赖满足/失效", "state"),
    ("loop", "completion", "提出交付时"), ("completion", "loop", "缺口与补救", "data"),
    ("board", "completion", "成果及证据引用", "data"), ("scheduler", "loop", "执行节点")], "默认单 Agent 循环；规划、委派和并发分别按需启用。完成核验是任务语义与真实证据核对。")

node("agent.factory", "统一实例工厂", "把获准定义/角色与子任务契约创建为隔离运行实例。", "AgentFactory.create", "定义版本、目标、引用、有效权限/模型与预算", "AgentInstance / allocation result", "定义创建不启动实例；重复请求不创建第二实例。", "agent")
VIEWS["agent"]["nodes"].insert(1, "agent.factory")
VIEWS["agent"]["edges"] = [e for e in VIEWS["agent"]["edges"] if not (e["source"] == "agent.definitions" and e["target"] == "agent.loop")]
VIEWS["agent"]["edges"] += [edge("agent.definitions", "agent.factory", "读取启用定义版本", "data"), edge("agent.collaboration", "agent.factory", "invoke经合法契约创建"), edge("agent.factory", "agent.loop", "固定定义后的实例运行", "lifecycle")]

parts("agent.definitions", [
    ("designer", "角色设计方法", "主Agent按需加载短方法生成职责、条件与验收草案。", "design_definition", "用户创建要求、现有角色、能力摘要", "AgentDefinitionDraft", "不强制另起设计Agent，不擅存临时角色。"),
    ("validator", "定义与授权校验", "检查会话归属、名称、依赖、权限请求与用户来源。", "validate_definition", "定义草案与可信上下文", "可提交草案或阻碍项", "用户指定来源由服务核对，模型引用不自行证明授权。"),
    ("model_intent", "模型意图解析", "保留inherit/用户explicit/授权auto并交Model核对。", "resolve_model_intent", "原指定名称及来源、父模型政策", "规范ModelRequest或缺口", "型号缺失回当前LLM，不暗换型号。"),
    ("repository", "定义提交与版本", "按批量策略保存定义，保持幂等、名称唯一与CAS。", "commit_definition", "已验证定义、稳定请求键、预期版本", "DefinitionVersion / per-item result", "定义是配置，提交不创建执行实例。"),
    ("discovery", "会话Agent发现", "按scope展示角色摘要，语义匹配任务与正反条件。", "discover_agents", "当前任务与可见定义", "有版本候选摘要", "候选发现不等于调用；use_when不是词典路由。"),
    ("change_service", "配置变更与撤销", "显示角色差异并基于当前版本生成反向修订。", "diff/disable/revert", "定义版本、用户选定变更", "新定义版本/冲突", "撤销配置不逆转已发生的外部动作。"),
], [("designer", "validator", "用户授权创建的草案", "data"), ("validator", "model_intent", "必要模型意图核对"),
    ("model_intent", "repository", "合法/未解决结果", "data"), ("repository", "discovery", "已启用定义摘要", "data"),
    ("repository", "change_service", "版本化配置", "data"), ("change_service", "repository", "反向修订/CAS", "state")], "用户要求创建时主Agent加载方法并调用create；后续语义发现合适角色，invoke另经统一工厂启动。")
VIEWS["agent.definitions"]["nodes"].append("agent.factory")
VIEWS["agent.definitions"]["edges"].append(edge("agent.definitions.discovery", "agent.factory", "当前LLM决定委派后，经Tool调用invoke"))
VIEWS["agent"]["edges"].append(edge("agent.definitions", "agent.loop", "Context提供会话候选，非自动调用", "data"))

parts("context", [
    ("sources", "来源解析", "读取有权限的原文、文件、Task Board、产物与外部材料。", "resolve_sources", "目标、scope、引用版本", "SourceManifest", "本地材料走 Workspace 授权适配器。"),
    ("rules", "规则与信任装配", "装配用户、项目、技能与角色规则并记录优先级。", "resolve_rules", "可信规则来源与作用域", "InstructionSet", "网页/工具文本不会自动变为高优先级指令。"),
    ("ingestion", "摄取与索引发布", "解析、切片、索引、发布；增量更新和删除传播。", "ingest/publish/delete", "来源版本、内容、授权", "内容块与 active revision", "未准备好的新索引不能混入当前有效版本。"),
    ("retrieval", "资料检索与证据", "权限内关键词/向量检索、排序与覆盖检查。", "retrieve", "查询、过滤、scope、预算", "版本化证据引用", "召回相关不证明来源真实；少量资料可直接读取。"),
    ("memory", "记忆生命周期", "候选、冲突、写入、召回、遗忘与派生删除。", "remember/recall/forget", "用户显式要求/候选、记忆政策", "Memory revision", "用户偏好不能授予权限；未核验结论不升为共享事实。"),
    ("selection", "选择与上下文预算", "按 purpose 选块并预留输出及工具反馈空间。", "select/allocate", "候选块、模型限制、任务目标", "选中块与分配计划", "不按固定回合裁剪所有任务。"),
    ("compression", "压缩与关键项保护", "压缩继续执行状态，核对目标、数字和来源。", "compress/validate", "固定输入与保留项", "ContinuationState", "真实审批与执行状态回 Runtime 读取。"),
    ("composer", "装配与快照", "分区稳定规则/历史/实时材料，产出可追溯上下文。", "compose", "选中块、指令、压缩状态", "ContextSnapshot / Manifest", "缓存不能改变用户目标、时间或有效工具权限。"),
    ("references", "引用登记与解析", "定位网页、内容、文件、产物、测试报告的实际版本。", "register/resolve/read", "来源与位置、hash、可见范围", "Reference / Citation", "不编造来源；不可用时给出明确状态。"),
], [("sources", "ingestion", "新增/更新材料"), ("ingestion", "retrieval", "已发布索引", "data"),
    ("sources", "retrieval", "明确来源或查询"), ("retrieval", "selection", "证据候选", "data"),
    ("memory", "selection", "允许读取的记忆", "data"), ("rules", "composer", "可信指令", "policy"),
    ("selection", "compression", "需要压缩时"), ("selection", "composer", "无需压缩的块", "data"),
    ("compression", "composer", "核验后继续状态", "data"), ("sources", "references", "登记来源"),
    ("references", "composer", "定位与版本", "data")], "资料、记忆与规则是不同支路，最终按当前任务目的装配；不是先跑完整 RAG 再回答。")

parts("tool", [
    ("registry", "工具注册与版本", "存完整 ToolSpec，向量库保存派生检索表示。", "register/update", "已启用 ToolSpec、能力/效果元数据", "Registry revision", "向量命中不能代替 schema 或当前授权。"),
    ("discovery", "工具发现与筛选", "角色/flag/权限缩小候选，关键词/向量召回后让 LLM 选择。", "discover", "目标、范围、候选预算", "可见 schema 与候选依据", "小工具集可直接暴露，索引只是发现方法。"),
    ("invocation", "调用闸门与派发", "统一参数、授权、审批复核、预算与适配器调用。", "invoke", "ToolCall + trusted context", "标准 ToolResult", "模型不能写入 approved/principal 等可信字段。"),
    ("effects", "调用与副作用账本", "持久意图、尝试、稳定业务键和未决结果。", "record_intent/reconcile", "action_id、参数hash、幂等键", "confirmed/pending/unknown", "超时不证明失败，不盲重试未知外部写入。"),
    ("failure", "失败恢复与等价切换", "分类错误、退避、熔断和有限等价提供方切换。", "recover", "类型化错误、剩余deadline", "恢复结果或能力缺口", "非等价替换必须交给 Agent 重新决定。"),
    ("mcp", "MCP 连接与适配", "协商、能力发现、会话生命周期和结果规范化。", "connect/discover/call/close", "已授权 provider 配置引用", "命名空间能力与协议结果", "连接不授信，重连不重放未知写调用。"),
    ("adapters", "领域与外部适配器", "转发到 Workspace、控制工具或第三方 API。", "dispatch", "已准入的调用", "原始结果及效果状态", "平台凭据不进入任意任务代码。"),
    ("results", "结果规范化与分页", "区分业务失败/基础设施失败，保存大结果引用。", "normalize/page", "原始输出、执行状态", "ToolResult / raw_ref", "HTTP200 或成功文字不能证明业务成功。"),
    ("audit", "执行审计与指标", "关联审批、真实动作、用量与类型化失败。", "audit/observe", "调用版本、结果、关联IDs", "事件与受控诊断引用", "不保存凭据；执行审计不依赖模型自述。"),
], [("registry", "discovery", "当前可见能力", "data"), ("discovery", "invocation", "LLM选择后调用"),
    ("invocation", "effects", "执行前登记意图", "state"), ("effects", "adapters", "准入后的调用"),
    ("adapters", "mcp", "MCP提供方路径"), ("mcp", "registry", "能力及schema版本", "data"),
    ("adapters", "results", "实际返回", "data"), ("results", "effects", "确认/待核对", "state"),
    ("results", "failure", "错误或未决反馈"), ("failure", "invocation", "允许重试/等价切换"),
    ("results", "audit", "结果与用量", "state")], "工具动作有统一入口，具体状态仍由所属 Runtime 实现；失败恢复集中在 Tool。")

parts("workspace", [
    ("binding", "项目绑定与本地授权", "配对设备/Runner，明确项目根与读写执行范围。", "bind/check_scope", "用户选定项目与权限", "ProjectRootBinding", "上传路径、符号链接或子目录不能绕过根边界。"),
    ("base", "输入基础状态", "指定提交或包含未提交修改的工作目录快照。", "capture_base", "用户工作目录/选定revision", "BaseStateSpec", "记录来源，不遗漏用户正在编辑的内容。"),
    ("isolation", "隔离与分支", "授权本地副本、worktree或可选云沙箱。", "allocate/release", "基础状态与所需隔离", "WorkspaceHandle", "如需原项目执行，明确冲突策略与实际隔离能力。"),
    ("environment", "环境准备与回收", "检测现有工具链、受控补依赖、健康检查。", "inspect/ensure/release", "模板、项目要求、预算", "EnvironmentManifest", "项目依赖与 Runtime 服务环境分开，全局安装另授权。"),
    ("process", "文件与进程执行", "受控读写、安装、测试、预览及进程停止。", "read/write/exec/poll/stop", "工作区句柄、命令、deadline", "执行证据与实际改动", "任意代码前后采集改动，不能漏掉shell写文件。"),
    ("changes", "变更与冲突合并", "采集ChangeSet、检查用户并发改动、生成合并或反向修改。", "changes/merge/revert", "基础/当前版本与改动单位", "新revision或ConflictSet", "不覆盖用户后续修改；冲突需明确解决。"),
    ("artifacts", "产物与格式适配", "登记版本、引用，提供预览/下载/导出。", "register/preview/export", "真实成果文件与版本", "ArtifactHandle", "存在可打开不等于内容质量合格。"),
    ("review", "审阅与局部接受", "按格式能力提供diff、位置反馈、接受/拒绝。", "review/accept/reject/revise", "固定 ReviewSet 与用户意见", "Delivery 状态与新用户修订", "不支持块级接受的格式明确只支持整份。"),
], [("binding", "base", "获准的项目"), ("base", "isolation", "基础快照", "data"),
    ("isolation", "environment", "环境生命周期", "lifecycle"), ("environment", "process", "ready后的操作"),
    ("process", "changes", "前后快照与真实改动", "data"), ("changes", "artifacts", "固定成果版本", "data"),
    ("artifacts", "review", "可审阅交付", "data"), ("review", "changes", "局部接受/撤销/冲突"),
    ("process", "environment", "停止与保留策略", "lifecycle")], "本地项目首版可用是产品目标；图不代表 Runner 已实现。交付、用户接受和外部发布是不同操作。")

parts("model", [
    ("catalog", "可见模型目录", "平台启用的模型、能力、版本和可用状态。", "list/resolve", "用户scope与平台配置", "可用模型候选", "目录可缓存，调用仍复核当前状态。"),
    ("policy", "选择与模型继承", "固定用户选择，子定义仅用户显式覆盖；Auto限定范围。", "resolve_policy", "用户选择、父政策、子显式要求", "EffectiveModelPolicy", "技能/角色不能覆盖用户选定模型。"),
    ("capability", "兼容与Auto选择", "检查工具/结构/多模态能力，Auto可用时才路由。", "check/select", "有效政策、能力需求与预算", "兼容调用配置或缺口", "不可用回到Agent/用户，不偷偷降低模型。"),
    ("gateway", "调用网关", "统一入口，管理服务凭据、限流、deadline。", "generate", "ContextSnapshot与调用配置", "带关联ID的模型尝试", "供应商差异明确呈现，统一接口不伪装全兼容。"),
    ("adapters", "供应商协议适配", "消息、工具schema、流式输出与实际前缀缓存接口。", "provider_call", "支持的参数与版本", "标准输出与usage", "能力/计费依官方协议核对，不假设KV可控。"),
    ("recovery", "调用恢复", "超时、限流、协议失败的有限重试。", "recover", "attempt错误、剩余预算", "新attempt或明确失败", "流式重试不拼接两次输出；固定模型不静默切换。"),
    ("usage", "计量与版本记录", "真实模型/参数、缓存用量、所有尝试费用。", "record_usage/settle", "provider usage与预留", "账本结算、模型调用记录", "未知账单待核对，不能按成功调用数漏算失败。"),
], [("catalog", "policy", "可见模型", "data"), ("policy", "capability", "继承后的约束", "policy"),
    ("capability", "gateway", "获准兼容配置", "data"), ("gateway", "adapters", "实际请求"),
    ("adapters", "recovery", "调用失败"), ("recovery", "gateway", "有限新尝试"),
    ("adapters", "usage", "实际用量和版本", "state")], "默认所有 Agent 继承用户选择；成本优化与故障恢复都遵守这一政策。")

parts("run", [
    ("history", "历史与输入权威", "存不可变用户消息、关联任务与会话。", "append/read", "原文与用户控制", "InputRef / History", "云/本地权威尚待选定，执行位置不决定存储位置。"),
    ("state", "Run 与交互项", "生命周期、Item revision、结果状态。", "transition/emit_item", "预期版本与领域确认", "RunState / InteractionItem", "模型finish不能跳过必需的证据核验。"),
    ("events", "事件与重连", "追加关键事件，序号续接、去重与快照。", "append/subscribe/replay", "带关联IDs的变化", "stream_seq与cursor", "事件回放不重新调用工具，不能被采样丢失关键状态。"),
    ("budget", "预算与准入", "任务总预算、子预算预留、使用结算、活跃Run上限。", "reserve/settle/release", "动作估算、已用额、deadline", "预留凭据或限额结果", "重试/子Agent/汇总都计入总额，队列有界。"),
    ("approval", "审批与用户控制", "持久审批、steer/enqueue/replace/cancel/partial。", "control/decide_approval", "用户或受授权独立代审决定", "ApprovalRef / ControlReceipt", "assisted/manual/automatic不扩大真实权限。"),
    ("checkpoint", "恢复边界与版本", "记录领域引用、账本游标、计划与环境版本。", "checkpoint", "已提交进度与未决动作", "Checkpoint", "不承诺跨外部系统原子快照。"),
    ("resume", "租约与执行恢复", "防双领，核对版本、当前授权、未决调用后继续。", "acquire/resume", "checkpoint和当前状态", "恢复节点或明确受阻", "非兼容版本不强行续跑；rerun是新Run。"),
    ("cancel", "取消传播", "阻止新调度，停止可取消进程与工具，保留已得成果。", "cancel", "范围与取消原因", "各执行器回执/未决项", "停止等待不等于外部动作已撤销。"),
    ("trigger", "未来触发器", "定时/事件创建或唤醒Run，和节点调度分开。", "trigger", "授权TriggerSpec与幂等键", "新Run或受控续接", "先预留，不默认允许自动创建定时任务。"),
], [("history", "state", "原始请求", "data"), ("state", "events", "可见状态变化", "state"),
    ("budget", "state", "准入/超限", "policy"), ("approval", "state", "干预安全边界", "state"),
    ("state", "checkpoint", "已提交领域进度", "state"), ("checkpoint", "resume", "恢复引用", "data"),
    ("resume", "state", "核对后继续", "lifecycle"), ("approval", "cancel", "用户取消"),
    ("cancel", "state", "取消回执与未决动作", "state"), ("trigger", "state", "授权触发", "lifecycle")], "Run 负责可靠控制；计划/记忆/工具结果仍由各自领域写入，不复制第二套业务权威。")

parts("support", [
    ("configuration", "配置与账号控制层", "管理员配置模型/API/政策；私人连接由用户授权。", "publish_config/connect/revoke", "平台管理与账号授权", "版本配置、凭据引用", "管理API不暴露为普通Agent工具；撤销当前生效。"),
    ("extensions", "扩展包与版本发布", "技能、工具提供方、模板包的校验与升级。", "install/validate/activate/rollback", "不可变包与依赖", "ReleaseManifest", "安装不是授权，同版本内容不能偷偷变化。"),
    ("cache", "共享缓存设施", "key、依赖失效、在途合并、配额与指标。", "get_or_compute/invalidate", "领域声明的可复用输入", "缓存引用与命中结果", "领域决定有效性，缓存不储存唯一的审批/产物。"),
    ("observability", "运行观测", "关联模块调用、版本、错误、成本和尾延迟。", "observe/query_trace", "脱敏span/event/metric", "诊断视图与指标", "Trace不替代恢复日志，不收隐藏思维全文。"),
    ("evaluation", "离线质量评测", "固定真实任务集、隔离比较版本、人工校准。", "evaluate/compare", "candidate/baseline/dataset/environment", "切片对比与ReleaseGate", "不为每个用户请求执行；防止评测重放外部写入。"),
    ("stores", "存储适配与访问", "逻辑历史、对象、检索与缓存存储接口。", "repository/blob/index", "领域拥有的对象和scope", "持久引用与版本", "物理数据库选型另议，不共用无归属的万能状态表。"),
], [("configuration", "extensions", "有效政策与提供方", "policy"), ("extensions", "evaluation", "待发布候选", "data"),
    ("observability", "evaluation", "授权失败样本", "data"), ("evaluation", "extensions", "回归报告与发布门槛", "policy"),
    ("extensions", "cache", "版本/撤销失效", "lifecycle"), ("configuration", "cache", "账号/授权撤销", "lifecycle"),
    ("cache", "stores", "可淘汰派生存储"), ("observability", "stores", "受控诊断记录"),
    ("evaluation", "stores", "样本与对比版本", "data")], "共享设施各有统一入口；调用图显示逻辑职责，不要求新增多个服务或数据库。")

# Third-level views reuse domain ownership. Edges still describe optional paths.
parts("tool.invocation", [
    ("schema", "参数与可信上下文", "规范业务参数，可信身份/授权由服务端注入。", "normalize", "ToolCall与服务端上下文", "ValidatedCall", "模型参数不能覆盖执行主体。"),
    ("precheck", "执行预检", "当前权限、flag、风险、预算、deadline。", "precheck", "动作与资源版本", "允许/拒绝/需审批", "schema合法不等于允许执行。"),
    ("approval", "必要审批等待", "请求Run持久审批，受影响节点等待。", "request_approval", "绑定动作、参数hash、资源、有效期", "ApprovalRef / declined", "超时或没回复不算批准。"),
    ("recheck", "执行前复核", "重新检查参数、资源与当前撤销状态。", "recheck", "当前动作与审批引用", "可执行调用或stale", "TOCTOU变化需重新判断，不复用过期批准。"),
    ("dispatch", "意图登记与执行", "Tool效果账本先存意图，调用领域适配器。", "record_then_dispatch", "稳定业务键、预留、deadline", "confirmed/pending/unknown", "并行生成不能越过执行闸门。"),
    ("result", "规范结果与结算", "登记真实返回、分离业务失败、分页引用。", "normalize/settle", "实际返回与用量", "ToolResult与反馈", "unknown保留核对，不冒充failed后重发。"),
], [("schema", "precheck", "结构已校验"), ("precheck", "approval", "需要确认时"),
    ("precheck", "recheck", "已有有效授权时"), ("approval", "recheck", "明确批准后"),
    ("recheck", "dispatch", "复核通过后"), ("dispatch", "result", "真实执行返回", "data")], "这是一条动作的安全契约，不是固定业务任务流水线；拒绝和未知结果都回到Agent决策。")

parts("agent.collaboration", [
    ("contract", "子任务契约", "目标、输入、输出、验收、预算与权限交集。", "prepare_delegation", "父目标与独立子工作", "DelegationSpec", "检查协调成本，不凭复杂二字一律拆分。"),
    ("instance", "隔离运行实例", "固定定义、模型继承、临时上下文与工作区。", "spawn", "定义版本与子预算", "AgentInstance", "不共享可写临时状态。"),
    ("channel", "消息与受控引用", "分配、补充、有限询问、进度和结果引用。", "send/read", "带任务/节点/版本的消息", "可追踪AgentMessage", "不复制完整上下文或凭据。"),
    ("join", "结果核验与汇总", "检查必需子结果、证据和目标版本，CAS提交共享板。", "join", "NodeResult引用与状态", "整合结果/缺口", "缺失和失败不静默视为完成。"),
    ("handoff", "可选控制权交接", "Handoff Controller 用CAS交接唯一对话责任。", "handoff", "目标Agent、未完成状态、expected_lease", "新ControlLease或失败", "控制权不自动转移全部权限，首版不默认开启。"),
    ("cancel", "生命周期与取消", "父取消、限额、超深度、子失败回传。", "cancel/reconcile", "父子关联与未决调用", "回执与保留成果", "不可取消副作用仍需Tool对账。"),
], [("contract", "instance", "工厂校验后创建", "lifecycle"), ("instance", "channel", "运行与交互"),
    ("channel", "join", "子结果与证据", "data"), ("join", "contract", "缺口触发再决策", "data"),
    ("channel", "handoff", "需要转对话责任时"), ("instance", "cancel", "取消与超限", "lifecycle")], "delegate返回结果，父Agent仍负责用户对话；handoff另行移交控制权，不是普通子调用。")

parts("agent.completion", [
    ("contract", "语义交付契约", "原文目标、硬约束、可接受成果与证据要求。", "resolve_contract", "用户原文与已明确修订", "DeliveryContract revision", "LLM不能为完成而删掉必需目标。"),
    ("evidence", "真实证据收集", "选用测试、读取、来源核对或格式检查。", "select_and_request_checks", "成果与缺口", "检查/来源引用", "没有跑测试就不能说测试通过。"),
    ("semantic", "语义核对", "判断证据是否支持目标，标出缺口与限制。", "review", "契约与受测版本证据", "目标满足/部分/受阻", "不强制新增裁判Agent；主张不是事实证明。"),
    ("version", "版本与硬条件校验", "核实实际成果、必需检查、未决效果和预期版本。", "validate_proposal", "VerificationReport与当前revision", "允许提交或stale", "合并/撤销/局部接受可能需要重验。"),
    ("delivery", "提交交付", "Run核对终态，Workspace发布受控成果。", "commit_completion", "CAS完成提案", "完整/部分/受阻交付", "completed不一律等于succeeded。"),
    ("acceptance", "用户接受与迭代", "审阅、局部接受、位置反馈与二次修改。", "review_delivery", "固定ReviewSet与用户意见", "独立Delivery状态/新修订", "AI判断完成与用户认可分开。"),
], [("contract", "evidence", "按需要选择检查"), ("evidence", "semantic", "真实证据", "data"),
    ("semantic", "evidence", "发现缺口再验证"), ("semantic", "version", "完成提案", "data"),
    ("version", "delivery", "条件/版本通过"), ("delivery", "acceptance", "交付供审阅", "lifecycle"),
    ("acceptance", "contract", "用户修订目标", "state")], "成果存在、检查通过、语义满足和用户接受分别表达；验收策略随任务变化。")

parts("context.memory", [
    ("candidate", "记忆候选", "显式记住或后台推断候选。", "propose_memory", "用户输入、任务结果、来源", "待判断候选", "不要每句话都写长期记忆。"),
    ("policy", "范围与写入政策", "读取/贡献开关、范围、保留期、可信来源。", "check_memory_policy", "候选与用户控制", "允许写入或拒绝", "不因协作而默认共享私人资料。"),
    ("conflict", "查重与冲突", "精确槽位/条件和语义候选对比，保留纠正历史。", "resolve_conflict", "来源/时间/条件/版本", "版本化事实或待确认", "相似不等于相同，不混淆不同成立条件。"),
    ("store", "提交与召回", "权威提交后才宣称记住，按范围查找。", "commit/recall", "验证事实与policy", "MemoryRef / revision", "记忆不能成为授权凭证。"),
    ("forget", "遗忘与删除传播", "停止召回，清理派生摘要、索引与缓存。", "forget", "选择器、派生依赖、保留政策", "完成项/失败项/删除标记", "备份恢复要重放删除，物理期限明确。"),
], [("candidate", "policy", "用户/后台候选"), ("policy", "conflict", "允许写入"),
    ("conflict", "store", "核验后提交", "state"), ("store", "forget", "删除/过期/撤销", "lifecycle"),
    ("forget", "store", "停止召回与新版本", "state")], "显式要求及时提交并报告成功/失败；推断候选可后台核验。遗忘是可追踪动作。")

parts("tool.mcp", [
    ("provider", "提供方绑定", "消费控制层已启用配置与账号状态。", "resolve_provider", "provider_ref与调用scope", "可连接配置", "服务密钥不进入prompt。"),
    ("session", "协议会话", "协商、健康、有限重连与关闭。", "connect/health/close", "连接配置与deadline", "SessionHandle", "重连不重新执行未知写操作。"),
    ("capabilities", "能力规范化", "provider命名空间、schema与版本。", "discover/normalize", "远端能力清单", "ToolSpec / registry revision", "远端描述是数据，不是高优先级指令。"),
    ("invoke", "闸门后调用", "通过统一Tool调用闸门才使用远端会话。", "proxy_call", "已准入动作与稳定调用ID", "协议结果或类型化失败", "注册可见不等于现在有执行授权。"),
    ("invalidate", "变化与撤销", "断开、能力变更、授权撤销使绑定/缓存失效。", "invalidate_binding", "当前变化事件", "registry revision / revoked状态", "旧会话不能继续使用已撤销账号。"),
], [("provider", "session", "获准建立连接", "policy"), ("session", "capabilities", "发现当前能力"),
    ("capabilities", "invoke", "Tool注册/闸门后"), ("session", "invalidate", "变化或断开", "lifecycle"),
    ("invalidate", "capabilities", "需重新发现", "state")], "MCP会话由Tool管理，账号授权与凭据由控制层管理，两种生命周期关联但不混为一份状态。")

parts("run.resume", [
    ("lease", "取得运行租约", "使用预期版本，防同一工作重复领走。", "acquire_lease", "run/node及预期revision", "有限Lease", "多worker需要fencing，单进程先保恢复边界。"),
    ("versions", "版本兼容检查", "检查业务schema、定义、技能与环境manifest。", "check_compatibility", "checkpoint与当前实现", "兼容/迁移/受阻", "升级不能悄悄改变既有审批与模型政策。"),
    ("access", "重建连接与核验", "读取当前授权/撤销，重建非持久连接。", "rehydrate", "有效配置与资源引用", "可恢复句柄与范围", "checkpoint不保存可长期复用的密钥授权。"),
    ("effects", "Tool未决动作对账", "查询实际效果，保留不能确定的项。", "reconcile", "Tool账本游标与业务键", "实际效果状态", "先核对，再决定是否允许重试。"),
    ("workspace", "工作区实际版本", "检查用户并发修改、环境可用与产物版本。", "check_workspace", "保存的版本与当前Runner状态", "可继续/冲突/缺失", "不把旧快照冒充当前磁盘。"),
    ("continue", "恢复可运行工作", "更新恢复事件，继续未完成节点。", "resume_nodes", "核对后的领域状态", "Run进展或明确受阻", "replay不执行；rerun是新尝试。"),
], [("lease", "versions", "checkpoint读入"), ("versions", "access", "兼容检查通过"),
    ("access", "effects", "当前授权核验"), ("effects", "workspace", "未决项已有明确处理"),
    ("workspace", "continue", "版本/环境允许继续")], "恢复有明确核对边界；未决效果无法核实的依赖不能当成已成功继续。")


def validate():
    for id, n in NODES.items():
        if n["parent"]:
            assert n["parent"] in NODES, (id, n["parent"])
        assert n["description"] and n["guard"]
    for id, v in VIEWS.items():
        assert len(set(v["nodes"])) == len(v["nodes"]), id
        assert all(n in NODES for n in v["nodes"]), id
        for e in v["edges"]:
            assert e["source"] in v["nodes"] and e["target"] in v["nodes"], (id, e)
            assert e["kind"] in TYPES
    covered = set(n for v in VIEWS.values() for n in v["nodes"])
    assert covered == set(NODES), set(NODES) - covered
    for id in NODES:
        visited = set()
        while id:
            assert id not in visited, "parent cycle"
            visited.add(id)
            id = NODES[id]["parent"]


def mermaid(v):
    ids = {n: "n" + str(i) for i, n in enumerate(v["nodes"])}
    lines = ["```mermaid", "flowchart LR"]
    for n in v["nodes"]:
        lines.append('  ' + ids[n] + '["' + NODES[n]["label"] + '"]')
    for e in v["edges"]:
        connector = "-.->" if e["kind"] in ("policy", "lifecycle") else "-->"
        lines.append(f'  {ids[e["source"]]} {connector}|"{TYPES[e["kind"]]}：{e["label"]}"| {ids[e["target"]]}')
    return "\n".join(lines + ["```"])


def build():
    validate()
    design_map_path = ROOT / "design" / "design-map.json"
    if design_map_path.exists():
        design_map = json.loads(design_map_path.read_text(encoding="utf-8"))["nodes"]
        for id, n in NODES.items():
            if id in design_map:
                n.update(design_doc=design_map[id]["design_doc"], code_target=design_map[id]["code_target"])
    interface_map_path=ROOT / "contracts" / "interface-map.json"
    if interface_map_path.exists():
        interface_map=json.loads(interface_map_path.read_text(encoding="utf-8"))["nodes"]
        for id,n in NODES.items():
            if id in interface_map:n.update(interface_doc=interface_map[id]["interface_doc"],interface_count=len(interface_map[id]["interfaces"]))
    graph = dict(schema_version="0.2", architecture_version="0.10", date="2026-10-07",
                 status="设计稿，非已实现运行系统", types=TYPES, nodes=NODES, views=VIEWS)
    (ROOT / "architecture" / "graph.json").write_text(json.dumps(graph, ensure_ascii=False, indent=2), encoding="utf-8")
    out = ["# UAW 分层架构图谱", "", "状态：v0.10 目标设计。七个 Runtime 是逻辑边界，不是七个独立服务；图中所有执行能力均未因画图而成为已实现功能。", "",
           "[打开交互图](demo/uaw-architecture-map.html) · [主架构](ARCHITECTURE.md) · [本轮题集参考](NOTION_ARCHITECTURE_REVIEW.md) · [细节契约](ENGINEERING_COMPLETENESS.md)", "",
           "## 如何阅读", "", "- 第一层：大模块调用与反馈。第二层：每个 Runtime 内部职责。第三层：易出错部分的细化链路。", "- 箭头标清调用、数据/引用、状态/事件、权限/配置或生命周期。职责图允许反馈环，只有某一版任务依赖 DAG 必须无环。", "- 统一入口代表状态所有权与契约；面向模型的控制工具通过 Tool 入口分发，不把全部业务逻辑挤进 Tool。", "- 交互图点击节点看入口/输入/输出/约束，双击或点击“展开内部”进入下一层；关系筛选只隐藏显示，不改变设计。", "- 节点 ID、归属与联系来自 [graph.json](architecture/graph.json)，由 [build_atlas.py](architecture/build_atlas.py) 生成本文与交互页面，更新图应修改生成源后重建。", ""]
    for i, (id, v) in enumerate(VIEWS.items()):
        out += [f"## {i + 1}. {v['title']}", "", v["summary"], "", mermaid(v), "", "| 子模块 | 统一入口 | 输入 → 输出 | 关键约束 | 详细开发策略 |", "| --- | --- | --- | --- | --- |"]
        for n in v["nodes"]:
            d = NODES[n]
            design = f"[开发设计]({d['design_doc']})" if d.get("design_doc") else "待设计映射"
            if d.get("interface_doc"):design+=f" · [接口契约]({d['interface_doc']})"
            out.append(f"| {d['label']} | `{d['entry']}` | {d['inputs']} → {d['outputs']} | {d['guard']} | {design} |")
        out.append("")
    out += ["## 变更、失败和等待如何回流", "", "- 用户纠正：UI → Ingress → Run 原文/ControlRequest → Intent 新理解 → Agent 使相关计划/结果失效；未受影响成果继续保留。", "- 工具失败：Tool 分类与允许恢复 → Agent 观察缺口；改变能力或目标时由 Agent 再决策。", "- 审批等待：Tool 预检 → Run 持久审批 → Tool 再核验 → 真正执行，拒绝回到 Agent 选已允许方案。", "- 上下文不足：Context 分页/筛选/压缩保护 → Agent 按缺口补资料；不能用摘要证明工具已执行。", "- 用户改文件：Workspace 检测实际版本变化 → ChangeSet 冲突/报告失效 → Agent 重验或修订，保留用户编辑。", "- 执行恢复：Run 租约/兼容检查 → 当前授权 → Tool 未决效果对账 → Workspace 实际版本 → Agent 可运行节点。", "", "## 跨模块引用契约", "", "每条联系的概念载荷必须携带 scope、关联 IDs、实际版本与类型化失败。返回的引用由原领域保管，消费方检查当前可访问性；Trace 只串联诊断，不作为第二份权威状态。具体字段按首条真实任务细化，不宣称永久协议已稳定。", ""]
    (ROOT / "ARCHITECTURE_ATLAS.md").write_text("\n".join(out), encoding="utf-8")
    template = (ROOT / "architecture" / "explorer.template.html").read_text(encoding="utf-8")
    payload = json.dumps(graph, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    assert template.count("__GRAPH_JSON__") == 1
    (ROOT / "demo" / "uaw-architecture-map.html").write_text(template.replace("__GRAPH_JSON__", payload), encoding="utf-8")
    print(f"Built {len(NODES)} nodes, {len(VIEWS)} views, {sum(len(v['edges']) for v in VIEWS.values())} relationships")


if __name__ == "__main__":
    build()
