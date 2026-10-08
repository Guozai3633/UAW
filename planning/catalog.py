"""Authored development work packages. This file does not implement the runtime."""

MODULES={
 "foundation":("工程与集成","composition/application、公共契约与跨模块联调；不是新的Runtime。"),
 "support":("配置与共享设施","配置、仓储、凭据边界、缓存、观测、评测及能力包。"),
 "run":("Run Runtime","原文与历史、执行状态、审批、预算、取消、检查点和恢复。"),
 "model":("Model Runtime","用户模型政策、实际调用、协议能力、恢复和真实用量。"),
 "intent":("Intent Runtime","用户原文加工、正式理解、未知项与只读草稿提示。"),
 "context":("Context Runtime","规则、资料、引用、预算装配、记忆和压缩。"),
 "tool":("Tool Runtime","注册与发现、调用闸门、真实结果、失败恢复与MCP。"),
 "workspace":("Workspace与本地Runner","本地授权、输入快照、隔离、环境、进程、成果和变更。"),
 "agent":("Agent Runtime","根循环、会话角色、子实例、技能、规划、调度和完成。"),
 "product":("API与前端","身份入口、聊天、真实状态、用户控制、审阅和管理页面。"),
 "integration":("后续入口适配","推特等渠道适配保持独立，不改变UAW核心策略。"),
}

PHASES={
 "P0":dict(name="工程起步与基础边界",goal="让实际实现能启动、正确记账并调用用户选定模型。",gate="具备最小公共类型、可恢复的受理记录、配置/凭据隔离、固定模型真实调用和基础成本记录。",sample="不执行项目写操作：受理一个输入并用选定模型返回受控结果。",required=True),
 "P1":dict(name="单Agent完整闭环",goal="完成第一条真实本地任务，用户能看见并控制全过程。",gate="经本机授权读取项目、保留未提交修改、执行真实测试、展示实际Diff与成果、人工审批/取消、版本核验和用户审阅全部贯通。",sample="修改一个小型Python样例项目中的函数，运行已有测试，展示改动及真实检查证据。",required=True),
 "P2":dict(name="角色、子Agent与工作成果",goal="保存可复用角色并运行一个隔离子Agent，同时跑通办公和学术样例。",gate="create不执行、invoke有界执行、模型继承/明确覆盖、子失败与取消、受控共享/Join和三个领域样例可核验。",sample="复用API审查角色；比较用户文档生成引用报告；比较两篇论文的主张、证据和不足。",required=True),
 "P3":dict(name="语义规划与并行协作",goal="按实际收益启用steps/DAG、并行工具和多个子Agent，正确处理版本与写冲突。",gate="简单任务仍走单循环；DAG无环/依赖/资源约束、并行成本、隔离合并、局部接受/撤销、运行中改目标与同用户多会话冲突通过。",sample="并行研究独立材料再汇总；两个子任务修改隔离文件树后审阅合并。",required=True),
 "P4":dict(name="上下文、缓存与能力治理",goal="增加长任务效率、工具规模和产品控制，不破坏原有授权与模型政策。",gate="记忆关闭/删除、压缩关键项、权限内向量发现、缓存真实命中/失效、MCP撤销、配置生命周期、环境模板和Auto授权边界通过。",sample="重做相似报告验证复用；删除记忆/撤销连接后确认旧结果不可继续使用。",required=True),
 "P5":dict(name="恢复、评测与受控试用",goal="崩溃后安全续跑，有发布证据、试用入口和可定位的失败记录。",gate="恢复先取得租约并复核当前访问与效果，不能重放未知写；三个领域有验收与成本报告；部署资料齐备，扩展能力默认关闭。",sample="在工具派发、文件修改与流式返回等边界故障后恢复；收集用户接受/返工记录。",required=True),
}

# Decisions are scheduled work, not permissions requested in this documentation turn.
DECISIONS=[
 dict(id="D01",question="历史与运行状态采用云端权威还是本地权威？",before="P0-02",status="待确认",impact="决定持久化适配器、离线重放和部署模式；避免双主历史。",fallback="未确认可用测试仓储验证port；正式持久化/上线不能以测试内存仓储验收。"),
 dict(id="D02",question="开发主体和OIDC试用入口实际采用哪些身份部署配置？",before="P0-03",status="Authlib/OIDC技术主选，IdP待配置",impact="开发主体与后续账号登录分别配置；技术协议已选，IdP与部署仍需落实。",fallback="开发期可使用仅本机可达的明确开发主体；公网试用必须接真实OIDC会话认证，不能拿库存在冒充登录已可用。"),
 dict(id="D03",question="本机执行选择受控OS隔离，还是明确授权的原生模式？",before="P1-04",status="待确认部署能力",impact="决定Runner执行和安装边界，cwd/venv不能提供OS隔离。",fallback="没有实际exec授权/隔离能力时只开放读；真实代码任务不能假称完成。"),
 dict(id="D04",question="React/TypeScript/Vite与事件客户端的实际兼容组合是否通过？",before="P1-10",status="技术主选已设计，待版本锁定/联测",impact="前端主选React/TypeScript/Vite、Query/Router和fetch SSE，组件/边界见技术栈。",fallback="前置轮可用CLI/测试客户端推进；P1界面验收前锁定稳定版本并接真实API，不能用蓝图代替。"),
 dict(id="D05",question="首批上传与导出格式是哪几种？",before="P2-01",status="待确认最小范围",impact="决定解析/预览适配器；办公和论文样例要有可用材料入口。",fallback="建议文本/Markdown及论文PDF输入、Markdown报告输出；这是验收候选，不是最终格式承诺。"),
 dict(id="D06",question="模型、联网搜索及MCP试验采用哪些批准提供方？",before="P0-05",status="待管理员配置",impact="决定实际适配器和凭据；搜索/MCP进入对应轮时补其提供方。",fallback="模型真实连通前只标协议测试；搜索/MCP未配置保持关闭，不展示虚构结果。"),
 dict(id="D07",question="assisted/manual/automatic的用户文案与持续授权边界是什么？",before="P4-09",status="暂定语义待确认",impact="manual先实现；辅助审查/自动模式仍受管理员及本机权限上限。",fallback="未确认继续manual，不以未定义的自动审批替用户授权。"),
 dict(id="D08",question="哪些任务结果算可接受，成本/等待的发布上限是多少？",before="P3-08",status="需基线数据后约定",impact="决定多Agent/缓存/Auto是否值得默认启用，防止只以接口数量验收。",fallback="P0收集样例与验收表，P2形成基线，测试前记录阈值；没有证据不宣称提升。"),
 dict(id="D09",question="首期是否真的需要云沙箱、handoff和定时跟进？",before="P4-07",status="启用范围待确认",impact="相应契约和实现任务已安排；供应商、业务触发与产品启用分开。",fallback="本地任务先完成；未选云执行后端保持cloud旗标关闭，handoff/automations默认关闭。"),
 dict(id="D10",question="推特是请求渠道还是社媒业务产品？",before="P5-06",status="明确后续讨论",impact="只有范围明确后才能决定账号、发布、审核和成果反馈适配。",fallback="本轮仅规划适配边界；推特开发不成为独立UAW交付的前置条件。"),
 dict(id="D11",question="LangGraph局部循环能否满足UAW工具、审批和动作身份边界？",before="P1-11",status="LangGraph主选，待真实边界验证",impact="P1-07引擎/局部保存，P1-09人工审批后完成三个案例；P5补复合检查点与进程重启恢复。",fallback="最小工具调用/审批等待/重复节点动作去重需过关；失败保留证据并写ADR，asyncio回退接口不表示已有可运行回退。"),
]

ROUNDS=[]
def r(id,module,title,goal,deps,nodes,tasks,acceptance,dirs=(),deliverables=(),status="planned",scope="required",decisions=()):
    ROUNDS.append(dict(id=id,phase=id.split("-")[0],module=module,title=title,goal=goal,
      depends_on=deps.split(),nodes=nodes.split(),tasks=list(tasks),acceptance=list(acceptance),
      extra_code_dirs=list(dirs),deliverables=list(deliverables),status=status,scope=scope,
      decision_dependencies=list(decisions),implementation_evidence=[]))

r("P0-01","foundation","工程启动与最小契约","建立能启动的Python应用和依赖组装，避免先实现全部未来DTO。","","support",[
 "按技术主选建立uv/pyproject、composition/application，冻结核心兼容版本并定义启动/关闭流程。",
 "只实现首条任务需要的ID/Ref/Failure/Principal/Scope/RequestMeta和可信上下文，从统一schema核对字段。",
 "列出七Runtime的port注入边界；用能力可用状态区分未实现与真实功能。",
 "建立原始材料、手动改动、失败日志及验收结果的fixture目录，并记录待选型ADR。"],[
 "应用能启动/关闭，缺少必需配置返回可定位错误，不注册空实现工具。",
 "主体/批准字段不能从用户或模型参数写入可信上下文。",
 "形成首批开发、办公、学术任务验收表；代码目录和schema引用一致。"],
 ["src/uaw/","src/uaw/shared/","tests/fixtures/","docs/decisions/","ops/"],["启动命令与最小配置示例","首批场景验收表"])
r("P0-02","support","持久化、CAS、blob与事件提交边界","让受理/版本冲突和大内容存取有唯一权威。","P0-01","support.stores",[
 "PostgreSQL/SQLAlchemy为技术主选；按D01确定权威部署位置，实现Repository/私有Blob/Index port的最小实际适配器。",
 "实现主体隔离、不可变内容Ref、CAS和相同request_id不同参数冲突。",
 "让受理记录与Outbox在同域事务提交，消费事件可去重；不建立跨域巨型事务。",
 "提供故障后重读受理状态和blob摘要校验，用测试仓储做协议验证并明确其非生产性质。"],[
 "进程重启后受理/原文可读取，重复请求不生成重复Run。",
 "两个并发CAS只有一个成功，blob不因路径字符串越界读取。",
 "提交失败不会先广播成功事件，重复Outbox消费不重复交互项。"],
 ["tests/integration/persistence/"],["存储部署ADR","迁移与备份的最小操作说明"],decisions=["D01"])
r("P0-03","support","最小管理配置、凭据与功能旗标","从控制层向Runtime提供固定配置和当前撤销状态。","P0-02","support.configuration",[
 "登记模型/工具提供方、环境模板和审批政策的最小配置，支持验证后发布。",
 "实现CredentialStore port和秘密write-only输入，禁止进入模型上下文/日志/工作区。",
 "建立已认证开发主体与管理员入口；普通用户不能自报admin。",
 "发布能力旗标并在发现/调用/恢复处提供一致读取接口，未实现能力保持不可用。"],[
 "管理员可配置一个模型提供方，普通Agent无法修改目录或读回秘密。",
 "相同配置修订可稳定读取，安全撤销使尚未执行调用拒绝。",
 "关闭能力后直接伪造工具调用同样拒绝，不仅隐藏按钮。"],
 ["src/uaw/api/","tests/integration/configuration/"],["最小管理员CLI或受保护配置入口","旗标默认值清单"],decisions=["D02","D06"])
r("P0-04","run","受理、原文、状态、事件与资源账本","保存原文并以真实状态和用量驱动后续执行。","P0-02 P0-03","run run.history run.state run.events run.budget support.observability",[
 "实现Conversation/InputRecord/Run受理，原文追加保存，理解输出不能覆盖原文。",
 "建立Run/InteractionItem状态白名单、事件seq及稳定item ID。",
 "实现根预算预留/结算/释放，关联operation/trace/attempt并脱敏记录。",
 "提供有序读取/断点Cursor和取消标记的基础设施，终态提交仍受完成控制器约束。"],[
 "相同原文和请求ID重放得到同一个受理实体。",
 "非法状态跳转被拒绝，事件重复不改变已提交revision。",
 "失败attempt计入账本，未确定账单标pending，不能填0冒充免费。"],
 ["tests/integration/run/"],["受理和状态协议fixture","基础trace/usage记录"])
r("P0-05","model","固定模型真实调用与协议恢复","完整执行用户选择的模型，不做静默模型替换。","P0-03 P0-04","model model.catalog model.policy model.capability model.gateway model.adapters model.recovery model.usage",[
 "实现目录查询、固定政策解析、能力预检和一个真实提供方适配器。",
 "支持首个模型需要的文本/工具/结构输出协议，长输出保存完整Ref。",
 "预留调用预算，记录真实模型配置、所有attempt、usage与缓存Token。",
 "有界重试遵守固定模型政策；流式已有输出时避免重复拼接；Auto只保留关闭状态。"],[
 "真实指定模型返回结果与usage，不可用/协议不支持给明确失败。",
 "超时/解析失败不会切到另一模型，耗费及回执去重正确。",
 "主/子政策继承的基础测试通过，实际provider连通证据单独保存。"],
 ["tests/integration/model/"],["实际提供方连通记录","模型配置与用量示例"],decisions=["D06"])

r("P1-01","intent","正式任务理解与原文溯源","得到有版本、可纠正的TaskFrame。","P0-04 P0-05","intent intent.original intent.semantic intent.frame",[
 "从Run读取不可变原文和有效补充，装配短语义解析模板。",
 "提取目标、约束、成果和未解项；可复用主首次模型调用，禁止词典固定业务路由。",
 "校验引用和原文含义，CAS提交TaskFrame并发理解事件。",
 "理解错误保留原文，简单直答不要求先启动单独判断Agent。"],[
 "原文与理解分别可查，模型扩大目标被核验拦截或明确为未确认假设。",
 "输入不够时记录缺口，不默认最高成本执行。",
 "新输入使旧理解过期，旧提案不能覆盖当前revision。"],
 ["prompts/","tests/integration/intent/"],["任务理解fixture与模型实际输出样本"])
r("P1-02","context","最小上下文、规则和引用","为当前调用提供必要且有来源的输入。","P0-02 P0-05 P1-01","context context.sources context.rules context.selection context.composer context.references",[
 "实现History/Workspace/Board等Reader port，首轮仅装配实际已有输入与资料。",
 "按来源和作用域装配平台/用户/项目规则，资料不能升级为指令。",
 "按真实模型窗口分配输入/输出/工具保留，生成ContextSnapshot和Manifest。",
 "登记实际读取内容的Ref/Location；Workspace Reader在Runner准备好后接入，缺失先返回blocked。"],[
 "给定同源版本能重建输入依赖，未经读取的URL不能变成证据。",
 "关键用户约束及输出空间得到保护，越预算明确处理。",
 "项目/外部文本不能授予权限或修改用户模型政策。"],
 ["tests/integration/context/"],["最小上下文快照与引用fixture"])
r("P1-03","tool","工具目录与完整调用闸门","使模型提出的动作经过参数、权限、审批和真实结果处理。","P0-03 P0-04 P1-02","tool tool.registry tool.discovery tool.invocation tool.invocation.schema tool.invocation.precheck tool.invocation.approval tool.invocation.recheck tool.invocation.dispatch tool.invocation.result tool.adapters tool.results tool.effects tool.audit tool.failure",[
 "登记首个任务必要工具，先按角色/旗标/权限过滤小目录，再让LLM选择。",
 "实现normalize→precheck→必要审批→recheck→登记意图→dispatch→normalize/settle。",
 "建立动作/attempt/效果账本，unknown写先对账；先只实现安全同提供方恢复。",
 "接Runtime控制工具适配器；只把已经可执行的工具暴露给模型，向量发现和MCP后续完善。"],[
 "模型自报owner/approved、未知字段及禁用能力不能执行。",
 "批准后参数/资源变更会拒绝旧调用，业务失败不被HTTP成功掩盖。",
 "超时未知效果不盲重试，真实输出、审计和预算能互相关联。"],
 ["src/uaw/tool/control/","tests/integration/tool/"],["工具调用竞态/失败fixture","控制工具到Facade接线表"])
r("P1-04","workspace","Runner配对与项目授权","让本机项目访问来自真实用户选择和设备授权。","P0-03 P1-03","workspace workspace.binding",[
 "实现设备配对、真实主体确认、本机根选择句柄和项目绑定。",
 "采用D03确定的执行边界；签名命令、期限、fencing和能力交集逐次检查。",
 "实现本机范围检查，覆盖真实路径、链接及撤销；服务凭据不进入任务进程。",
 "开发期可用本机受控IPC适配Runner协议，网络长连接按试用部署方式补齐。"],[
 "聊天里任意路径字符串不能授予访问权，伪设备/旧签名不能执行。",
 "根外/链接越界访问被拒绝，撤销后新动作立即失效。",
 "实际OS隔离或明确原生授权有记录，不能用cwd/venv代替。"],
 ["apps/local_runner/uaw_runner/","tests/integration/runner/"],["配对与本机授权演示","执行能力报告"],decisions=["D03"])
r("P1-05","workspace","输入快照、隔离、环境和真实进程","运行真实项目检查并保留用户已有修改。","P1-04","workspace.base workspace.isolation workspace.environment workspace.process",[
 "采集获准已提交/未提交/未跟踪状态，超限/排除项明确报告。",
 "先实现隔离副本与获准原生后端，不要求首轮完整worktree/云沙箱。",
 "检查预装Python环境，登记实际依赖；安装未授权时保持关闭。",
 "实现file.read/write的摘要CAS与process.exec/poll/stop，采集stdout/stderr/退出码及进程树。"],[
 "初始未提交改动参与输入，任务完成后仍得到保留。",
 "实际运行样例已有测试，running/退出/超时/离线状态不混淆。",
 "旧摘要写入失败，停止无真实回执时不宣称stopped。"],
 ["src/uaw/workspace/backends/","apps/local_runner/uaw_runner/","tests/fixtures/projects/"],["真实项目与进程证据","输入快照清单"])
r("P1-06","workspace","实际变更、成果与基础审阅","用户能看见这次工作改了什么并恢复文件。","P1-05","workspace.changes workspace.artifacts workspace.review",[
 "对文件工具及shell修改采集before/after，登记实际ChangeSet。",
 "登记有Hash/来源/版本的成果，实现首个格式的预览与下载。",
 "提供按文件审阅、接受/拒绝/反馈；接受意见与真正应用修改分开。",
 "实现整文件版本恢复及当前内容冲突检查，改动后使旧验证失效。"],[
 "工具外命令造成的修改同样出现在Diff。",
 "用户后续编辑不会被合并/撤销盲覆盖。",
 "成果可打开，引用指向实际内容；无内容不能publish成功。"],
 ["tests/integration/delivery/"],["Diff/版本恢复演示","首个成果预览/导出样例"])
r("P1-07","agent","根实例、单Agent循环与工具接线","由主Agent动态决定下一步并完成实际工作。","P1-01 P1-02 P1-03 P1-05 P1-06","agent agent.factory agent.loop",[
 "实现根Agent Factory、预算和有效模型/权限绑定，不启用子树或默认DAG。",
 "用AgentEnginePort封装LangGraph StateGraph及PostgreSQL局部保存，执行build context→generate→验证建议→工具执行/等待→观察的循环。",
 "接必要控制工具与文件/进程操作，失败信息返回当前LLM继续决定。",
 "有限步数、deadline和用户取消能结束循环，LLM不能直接写completed。"],[
 "简单问题直接回答，多步项目任务确实调用工具而非模拟日志。",
 "步骤/工具次数有界，固定用户模型保持不变。",
 "缺能力或材料时等待/受阻并说明，不能用缓存结果伪装新执行。"],
 ["src/uaw/tool/control/","src/uaw/agent/engines/","tests/integration/agent/"],["真实单Agent任务运行轨迹"])
r("P1-08","agent","交付契约、证据和完成提交","以真实要求、实际检查和版本决定是否完成。","P1-07","agent.completion agent.completion.contract agent.completion.evidence agent.completion.semantic agent.completion.version agent.completion.delivery agent.completion.acceptance",[
 "从原文/修订形成Contract，逐要求收集命令、结构、引用和语义证据。",
 "接verification.run/report与tasks.verify，命令结果来自实际ProcessRecord。",
 "核对成果版本、证据覆盖和未知效果，生成DeliveryProposal再CAS提交终态。",
 "用户accept/reject/revise单独保存；不以用户接受补造测试通过。"],[
 "没有实际执行证据只能not_run/blocked，不能passed。",
 "必需要求缺失、成果过期或未知写时不得全部成功。",
 "交付partial有明确缺口；用户审阅与自动完成记录分别可查。"],
 ["tests/integration/completion/"],["逐要求验收报告","完成/部分完成/受阻反例"])
r("P1-09","run","人工审批、基础干预与取消","用户可停止或修正当前单Agent任务。","P1-07 P1-08","run.approval run.cancel",[
 "完成manual批准/拒绝/到期流程，参数Hash/目标版本与批准范围固定。",
 "接LangGraph interrupt/继续的当前审批复核，验证工具调用、批准等待和丢回执重入去重三个案例；完整重启恢复留给P5。",
 "单循环安全边界接收steer与取消，旧目标结果不贡献新目标。",
 "取消传播到正在执行工具/进程，已发生效果和费用保留并对账。",
 "记录可见等待/控制Item；辅助/自动模式仍关闭，复杂图修订留给P3。"],[
 "批准后资源改变需重新核验，拒绝/超时不等于授权。",
 "停止有真实回执，失联/unknown如实等待而不是假完成。",
 "运行中纠正能作用于下一安全边界，原文和历史不被覆盖。"],
 ["tests/integration/control/"],["manual审批与取消演示"])
r("P1-10","product","最小API与真实聊天工作区","让用户从页面完成第一条任务和审阅。","P1-09","ui ingress",[
 "按D04锁定React/TypeScript/Vite稳定组合，FastAPI接主体检查/请求去重/资源归属与最小HTTP接口。",
 "接提交、模型选择、发送后TaskFrame浅色提示、Item/SSE续接、审批和取消。",
 "接本机项目选择、实际命令状态、Diff与成果预览/下载，前端不解析模型文字猜状态。",
 "开发入口与真实账号试用认证分开；有趣状态文案只作为展示槽位，不影响状态语义。"],[
 "从页面发起实际任务，刷新/断连续接不重复提交或重复项。",
 "能批准/取消、查看真实退出码及文件变化；理解提示不覆盖原文。",
 "未实现能力不显示可用；未使用真实账号认证的入口不对公网开放。"],
 ["src/uaw/api/","apps/web/src/features/chat/","apps/web/src/features/workspace/","apps/web/src/features/review/","apps/web/src/features/approvals/"],["可操作开发页面","HTTP/Item/SSE接线说明"],decisions=["D04"])
r("P1-11","foundation","第一条真实任务阶段验收","证明从用户输入到检查、变更和接受完整可用。","P1-10","",[
 "用已确认fixture经真实模型、本机授权、真实文件和测试完成代码任务。",
 "覆盖测试失败、缺依赖、取消、手动改文件、权限撤销和模型不可用。",
 "保存实际模型/工具/环境版本、总尝试费用、耗时和用户审阅记录。",
 "登记未过项及责任轮，P1未过不能宣称首个闭环完成。"],[
 "成功及失败轨迹均可复查，运行证据不是mock、HTML动画或schema示例。",
 "用户原有改动保留，未运行检查没有被写成通过。",
 "具备可重复演示命令及阶段报告，基础未过项修完后进入P2。"],
 ["tests/integration/scenarios/","docs/implementation/"],["P1阶段验收报告","实际运行Ref与成本记录"],decisions=["D11"])

r("P2-01","context","文件上传、摄取与索引发布","把用户办公材料和论文变成可定位、可删除的资料。","P1-11","context.ingestion context.retrieval",[
 "按D05实现最小上传/格式检查/解析器，记录原资产和页/段位置。",
 "切分并建立批准profile的检索索引，构建验证后CAS发布active版本。",
 "提供状态查询、混合或基础关键词召回和引用定位，未发布数据不混入。",
 "删除原材料使索引/派生引用失效；格式失败说明缺口，不静默裁成完整材料。"],[
 "办公/论文样例内容可检索并回到实际位置。",
 "过期/删除来源不再召回，来源隔离和新旧发布竞态通过。",
 "上传回执只在真实字节/Hash检查后产生。"],
 ["src/uaw/context/","tests/fixtures/materials/"],["上传/解析/发布样例","首批格式支持矩阵"],decisions=["D05"])
r("P2-02","tool","联网搜索与网页读取","通过管理员提供方获取可核验外部资料。","P2-01 P0-03","tool.adapters tool.results context.references",[
 "接一个已配置搜索提供方及web.read，普通用户不设置API key。",
 "校验DNS/重定向与获准网络范围，搜索摘要和实际读取分开。",
 "记录URL、抓取时间、实际内容版本与可定位引用，处理大结果分页。",
 "提供未配置、限流、无内容和失效链接的真实失败反馈。"],[
 "实际读取的内容才可作为结论引用，snippet不冒充全文。",
 "秘密不出现在模型结果，根外网络目标按政策拒绝。",
 "来源失败/时效不足会显示限制，不换非等价工具假称同证据。"],
 ["tests/integration/web_sources/"],["真实搜索/网页引用样例"],decisions=["D06"])
r("P2-03","agent","技能加载与可复用任务模板","让操作方法按需复用而不靠长主提示词。","P2-01","agent.skills context.rules",[
 "建立SkillSpec摘要发现和固定版本激活，完整方法按需加载。",
 "校验技能依赖/权限/禁用状态，脚本执行仍走Tool Runtime。",
 "实现TaskTemplate保存目标、来源、输出、验收及锁定字段，允许异常时动态判断。",
 "区分RoleProfile、ToolSpec、SkillSpec；只实现当前需要的builtin方法。"],[
 "未使用技能不加载全部正文；已激活版本和输出要求可查。",
 "技能文本不能扩大权限、替换用户模型或修改锁定要求。",
 "成功任务可按同模板复用并保留必要动态探索。"],
 ["capabilities/builtin/","tests/integration/skills/"],["最小技能包/模板样例","加载版本记录"])
r("P2-04","agent","会话子Agent定义的设计和版本管理","用户可用自然语言创建、修改和撤销角色。","P2-03 P0-05","agent.definitions agent.definitions.designer agent.definitions.validator agent.definitions.model_intent agent.definitions.repository agent.definitions.discovery agent.definitions.change_service",[
 "主Agent按需加载精炼设计方法，生成职责、use_when/avoid_when和输入/输出契约。",
 "实现agents.create/update/list以及批量atomic/independent、名称与项幂等校验。",
 "默认inherit，explicit必须来自真实用户且目录可用；缺模型反馈needs_resolution。",
 "绑定当前会话并记录不可变定义版本，支持diff/disable/revert，create不启动实例。"],[
 "一句话创建多个角色可逐项核验，会话间定义不会越界发现。",
 "显式缺失模型不会静默换主模型，模型伪造用户来源被拒绝。",
 "恢复旧定义创建新revision，运行实例不会追随定义新版本。"],
 ["src/uaw/agent/definitions/","src/uaw/tool/control/","prompts/"],["自然语言创建角色演示","角色变更/批量失败fixture"])
r("P2-05","agent","首次有界子Agent调用","把定义转换为独立上下文和受限执行实例。","P2-04 P1-09","agent.collaboration agent.collaboration.contract agent.collaboration.instance agent.collaboration.channel agent.collaboration.cancel agent.factory",[
 "主循环提供会话候选摘要，由当前LLM根据任务决定是否agents.invoke。",
 "先运行一个有界子任务；Factory切分父预算、继承模型并求权限交集。",
 "隔离上下文和必要工作区，通过引用消息、wait和cancel收集结果。",
 "更新Run取消传播与子树状态，默认不启用任意递归或并行写。"],[
 "创建角色后不自动invoke，简单任务仍可单Agent完成。",
 "子实例不能看到未授权父完整历史或取得比父更大的权限/预算。",
 "重复creation_key不重复启动，子失败/取消和真实费用父侧可查。"],
 ["src/uaw/agent/collaboration/","tests/integration/subagents/"],["单子Agent真实运行轨迹","隔离/继承/取消反例"])
r("P2-06","agent","共享结果板与Join","父Agent可靠收集结果并保留最终交付责任。","P2-05","agent.board agent.collaboration.join",[
 "实现候选/确认结果BoardEntry及依赖版本CAS，不共享可变提示词。",
 "子返回AgentResult，Join校验目标、实际证据、版本和未完成项。",
 "结果冲突/过期返回主Agent重新判断，失败可以部分交付但必须明示。",
 "父最终综合仍经过P1完成核验，子completed不等于整个Task成功。"],[
 "旧Task版本的子结果不会污染当前目标。",
 "并发提交同板条目出现明确冲突，来源可追溯。",
 "子失败及证据不足不会被父汇总改写成全部成功。"],
 ["tests/integration/join/"],["共享板与Join演示"])
r("P2-07","agent","办公与学术方法和成果验收","在通用架构上实现两个可复用工作场景。","P2-02 P2-03 P2-06","agent.skills agent.completion.semantic context.references",[
 "实现文档比较/报告方法和学术主张、证据、假设、冲突整理方法。",
 "以RoleProfile/SkillSpec配置职责与工具上限，不按行业词典强制派发。",
 "普通报告与论文讨论输出带定位引用、推断标记和缺口，只有需要时用子Agent。",
 "核对builtin配置与当前invoke契约；未覆盖字段先修契约，不私加工具参数或自动保存用户角色。"],[
 "办公样例形成可编辑报告，用户能核对来源并提出修改。",
 "学术样例区分原文主张/模型推断/未验证假设，不虚构文献或实验。",
 "同一模型政策作用于理解、子任务和评审，领域方法可关闭/替换。"],
 ["capabilities/builtin/office_report/","capabilities/builtin/academic_discussion/","tests/fixtures/scenarios/"],["两种builtin方法与样例成果","领域验收表"])
r("P2-08","product","角色与子任务页面","用户可查角色、修改配置并了解子任务结果。","P2-07 P1-10","ui ingress",[
 "展示会话角色摘要、版本、模型继承/明确覆盖和实际可用状态。",
 "接创建/变更/恢复角色的结果，缺模型/权限时提供明确纠正路径。",
 "展示子任务目标、等待/失败和成果，不把内部私密思维全文放进页面。",
 "把工具与会话绑定、消息及取消结果接为稳定Item，默认界面保持聊天/成果为主。"],[
 "用户知道保存角色与启动任务是两个动作。",
 "指定子模型可查真实配置；修改定义不改变在跑实例。",
 "子失败/受阻易发现且可停止，普通用户无需理解内部节点才能使用。"],
 ["apps/web/src/features/agent_definitions/","apps/web/src/features/run_controls/"],["会话角色/子任务可用页面"])
r("P2-09","foundation","三类工作与单子任务验收","形成独立UAW的基础产品证据。","P2-08","",[
 "通过真实页面运行代码、文档报告、论文比较及有界子任务。",
 "记录用户接受/反馈/修订和包括所有失败尝试的费用。",
 "建立单Agent基线与有子任务方案的同材料比较，暂不宣称多Agent收益。",
 "验收失败回对应模块修复后再进入并行增强。"],[
 "三类任务均有原始材料、实际成果、引用/测试和审阅证据。",
 "角色复用与模型继承可复现，缺证据有如实限制。",
 "有可用基线供P3的成本/质量判据使用。"],
 ["tests/integration/scenarios/","docs/implementation/"],["P2验收与基线报告"])

r("P3-01","agent","语义执行评估与步骤计划","独立判断规划、委派、并发和信息缺口。","P2-09","agent.assessment agent.planning intent.references intent.probe intent.ambiguity",[
 "按需装配ExecutionAssessment输入，可复用首次调用，不建立常驻分类Agent。",
 "实现none/steps、single/parent_child、serial/parallel与工具/Agent并发范围校验。",
 "支持有界只读探查、指代消解、关键歧义澄清和得到新证据后复评。",
 "steps记录目标/验收和状态，但不因为有步骤就自动创建子Agent。"],[
 "简单、紧耦合、独立探索及缺材料样例采用不同合理方案。",
 "用户要求单Agent/先计划得到遵守，不因词长选最高规格。",
 "结构错误有界修复，不能静默改枚举后假设全部建议有效。"],
 ["prompts/","tests/fixtures/assessments/"],["执行评估对照样例","步骤计划实际轨迹"])
r("P3-02","agent","DAG验证与有界调度","以真实依赖和资源执行任务图。","P3-01","agent.scheduler agent.planning",[
 "实现TaskGraph提交/PlanPatch、节点ID/依赖/环/缺输入校验。",
 "调度就绪节点，按Run账本预留并发资源、队列和deadline。",
 "节点状态独立持久化，失败/取消/失效传播到依赖后继。",
 "图仅在需要时生成；Node不等于Agent，每个节点是否委派另行决定。"],[
 "环、缺失依赖、已过期输入和资源不足不能被调度。",
 "前序成果实际确认后后继才执行，同节点不被重复领取。",
 "计划修改不抹去旧费用和外部动作。"],
 ["tests/integration/scheduler/"],["DAG与修订失败fixture"])
r("P3-03","tool","独立工具并发与回压","只并发可证明独立的动作，并保持账本正确。","P3-02","tool.invocation tool.effects run.budget",[
 "在单Agent一步内并发获准独立只读ToolCall，保留call/attempt关联。",
 "实现并发上限、预算预留、慢调用等待、deadline和取消回压。",
 "写操作按有效范围及冲突策略串行或隔离，不因LLM声明独立而放行。",
 "乱序回执按照调用ID归并，未知效果单独挂起对账。"],[
 "并发工具无需创建子Agent，结果乱序不串到其他调用。",
 "预算不足不先派发后记账，取消不停止其他合法等待者。",
 "同资源写竞态被阻止，超时不会盲重试写。"],
 ["tests/integration/tool_parallel/"],["工具并发与串行对照轨迹"])
r("P3-04","agent","多个子Agent并行与树级约束","运行多个独立分工并控制父子深度、预算和取消。","P3-02 P2-06","agent.collaboration agent.collaboration.instance agent.collaboration.channel agent.collaboration.join agent.collaboration.cancel agent.factory agent.board",[
 "支持多个有界子实例同时执行，专业/权限/模型和上下文分别绑定。",
 "限制树深、实例数及总预算，默认不开放无限递归。",
 "让Board/Join核对各子结果版本，子失败可修订计划或如实交付partial。",
 "树级取消停止新节点并对在途效果对账，父只在汇总核验后完成。"],[
 "两个独立子任务可同时运行，紧耦合工作仍可由单Agent完成。",
 "祖先取消、越深度/预算和角色撤销不会被子节点绕过。",
 "子完成、子失败与总任务成功区分清楚。"],
 ["tests/integration/agent_parallel/"],["并行子任务及树级取消演示"])
r("P3-05","workspace","并行写隔离与三方合并","把子工作区修改安全纳入用户项目。","P3-04 P1-06","workspace.isolation workspace.base workspace.changes",[
 "增加获准Git worktree及多隔离副本后端，记录真实基础和未提交内容。",
 "对多个writer分配独立工作区、写集合及控制租约；不把worktree当OS沙箱。",
 "三方比较base/子成果/用户当前版本，文本冲突反馈Agent或用户，二进制按文件。",
 "合并实际应用后产生新版本、ChangeSet和需重验清单。"],[
 "两个writer不直接写同一原生目录，当前用户编辑得到保留。",
 "冲突不静默覆盖，未过版本检查不会合并。",
 "非Git项目可使用副本路径，Git权限/基线缺失有明确受阻。"],
 ["src/uaw/workspace/backends/","tests/fixtures/git_projects/","tests/integration/merge/"],["隔离/冲突/三方合并演示"])
r("P3-06","workspace","块级审阅、局部应用与撤销","用户能选择具体改动和反馈位置。","P3-05","workspace.review workspace.changes workspace.artifacts agent.definitions.change_service agent.completion.version",[
 "建立稳定hunk/unit和位置反馈，按文件或可支持块粒度接受/拒绝。",
 "局部merge/revert校验当前Hash，冲突返回新审阅，不盲写。",
 "角色配置逆向修订保持历史，文件撤销和外部服务补偿不混用。",
 "修订/撤销传播证据失效并申请必要重验，前端提供可见新版本。"],[
 "选择部分单位只应用该部分，用户后续修改保留。",
 "版本漂移、二进制和不支持块级格式有正确降级。",
 "旧测试不能继续证明撤销后文件，配置恢复重新核验模型/权限。"],
 ["apps/web/src/features/review/","tests/integration/partial_review/"],["局部接受/撤销/反馈演示"])
r("P3-07","run","复杂运行干预与多会话任务","处理目标修订、排队、部分交付和同用户共享任务。","P3-04 P3-06","run.approval run.cancel run.history run.state agent.planning agent.board",[
 "完成steer/enqueue/replace/cancel/deliver_partial的不同语义。",
 "按影响范围修订Frame/Plan，使旧节点/结果失效并保留不受影响成果。",
 "显式关联同用户会话与Task，目标CAS、引用权限和写控制权分别核验。",
 "处理工具安全边界纠正、在途写对账及冲突提示，不做最后输入覆盖。"],[
 "改变目标不会删除已发生效果，先交现有成果有真实限制。",
 "两个会话同时改目标出现明确冲突，关联不自动取得写控制权。",
 "新目标不消费旧子成果，未受影响的已核验内容可复用。"],
 ["apps/web/src/features/run_controls/","tests/integration/multi_conversation/"],["五类用户控制与多会话冲突演示"])
r("P3-08","foundation","规划与并行收益验收","以真实结果证明复杂执行方式何时值得启用。","P3-03 P3-07","",[
 "在P2同样材料上比较单循环、steps、并发工具、并行子任务。",
 "记录接受率、返工、全部尝试成本、耗时和合并负担。",
 "依据D08预先登记的阈值决定默认启用范围；收益不明确保留能力但不默认启用。",
 "验证困难紧耦合任务不会因为复杂就强制多Agent/DAG。"],[
 "比较结果有实际材料/版本/费用及审阅记录，阈值未被事后改成通过。",
 "并发安全、取消、失效和用户改动保留通过。",
 "有明确默认策略及需要进一步验证的任务范围。"],
 ["tests/evaluation/","docs/implementation/"],["P3阶段与复杂度策略报告"],decisions=["D08"])

r("P4-01","context","记忆读写、冲突与遗忘","用户可控制任务是否读取或贡献记忆。","P3-08","context.memory context.memory.candidate context.memory.policy context.memory.conflict context.memory.store context.memory.forget",[
 "实现显式/推断候选、scope/保留政策、冲突槽及受控提交。",
 "读与贡献开关分开，推断不自动变成用户事实。",
 "支持召回、明确限定删除、索引/摘要/缓存失效及物理清理回执。",
 "将记忆来源、有效期和撤销暴露给用户，不扩大跨会话读取权限。"],[
 "关闭记忆读后派生缓存也不能提供旧记忆。",
 "冲突事实澄清或版本替代，不直接拼为一致结论。",
 "空选择器删除拒绝，获准遗忘后后续模型输入不再带旧内容。"],
 ["apps/web/src/features/workspace/","tests/integration/memory/"],["记忆开关/冲突/遗忘演示"])
r("P4-02","context","语义压缩、裁剪与稳定前缀","在长任务中保留关键要求和真实执行状态。","P4-01","context.compression context.selection context.composer",[
 "按purpose和真实窗口选择压缩/裁剪支路，不每轮执行所有策略。",
 "保护用户目标、硬约束、数字/路径、引用和未决动作，并核验摘要。",
 "生成新context epoch与依赖Manifest，旧快照不能继续向新纪元追加。",
 "稳定规则/角色/技能/工具schema顺序，动态输入置后；记录provider实际缓存Token。"],[
 "关键数字和授权/未完成状态在长上下文样例中不丢失。",
 "压缩输出不伪造来源或工具已执行，失效来源不能借摘要继续使用。",
 "前缀缓存命中根据实际usage记录，不能只根据文本相似声称命中。"],
 ["tests/fixtures/long_context/","tests/integration/compression/"],["压缩保留核验报告","前缀缓存实际观测"])
r("P4-03","tool","角色过滤与向量混合发现","扩大工具目录而保留LLM最终选择。","P4-02 P2-04","tool.registry tool.discovery agent.definitions.discovery context.retrieval",[
 "工具注册向量索引和关键词索引，配置批准embedding profile和目录修订。",
 "先角色/产品旗标/权限过滤，再混合召回与候选重排，返回必要schema。",
 "会话角色摘要支持语义匹配，最终invoke/tool选择仍由当前LLM决定。",
 "索引失效/未构建时回基础目录策略；对照小目录直接暴露的效果和成本。"],[
 "禁用/越权工具不会被向量检索复活，调用仍再次校验。",
 "新增/撤销版本与检索索引一致，大目录候选召回有样例证据。",
 "检索失败不默认最高规格，也不将相似度当授权或成功概率。"],
 ["tests/evaluation/tool_discovery/"],["注册/索引同步报告","工具发现对照结果"])
r("P4-04","support","多层结果缓存与在途合并","在不改变当前权限和结果语义的前提下减少重复工作。","P4-03","support.cache context.sources context.retrieval model.usage",[
 "实现解析/检索/上下文派生/获准只读结果缓存，绑定scope和全部版本依赖。",
 "实现single-flight，等待者取消独立，不合并写动作/审批/进程当前状态。",
 "处理bounded_age、短期负缓存和memory/连接/配置/文件变更的依赖失效。",
 "区分请求命中、实际有效命中、provider前缀命中及净成本/延迟。"],[
 "同主体同依赖可复用，跨主体私有内容不能共享。",
 "删除/撤销/改目标后旧缓存不可贡献当前结果。",
 "写幂等使用账本不使用结果缓存，等待取消不误停其他计算。"],
 ["tests/integration/cache/","tests/evaluation/cache/"],["缓存依赖/失效表","实际命中与收益报告"])
r("P4-05","tool","MCP与私人账号连接生命周期","可安装接入能力，但授权由真实账户和政策决定。","P4-04 P0-03","tool.mcp tool.mcp.provider tool.mcp.session tool.mcp.capabilities tool.mcp.invoke tool.mcp.invalidate tool.failure support.configuration",[
 "实现批准provider绑定、协议session、远端能力规范化和ToolRegistry发布。",
 "MCP调用仍走统一闸门、结果规范化及效果账本，不能直连绕授权。",
 "实现用户私人连接的授权/到期/撤销，与管理员平台API key分开。",
 "连接/能力变化使旧候选、session和缓存失效，stdio使用批准启动模板。",
 "完善超时/退避/熔断与严格等价提供方切换；非等价替换交回当前Agent判断并记录信息/效果差异。"],[
 "一个真实批准服务连通，过期/撤销后旧审批不能继续调用。",
 "远端描述/输出不能变成高优先指令，秘密不返回普通用户。",
 "断开/能力变化和大结果分页/未知写的失败分支有证据。",
 "等价契约/当前授权任一不满足都不能自动切换；未知写先对账，摘要工具不能冒充原文读取。"],
 ["tests/integration/mcp/","apps/web/src/features/workspace/"],["真实MCP连通/撤销演示"],decisions=["D06"])
r("P4-06","support","完整配置与能力包版本发布","管理员可验证、发布、停用和恢复配置或插件。","P4-05","support.configuration support.extensions",[
 "完善模型/提供方/政策/凭据/环境模板管理，stage/validate/activate与审计分开。",
 "实现bundle安装/依赖/Hash/能力验证、激活、撤销及旧版本回滚。",
 "运行固定内容版本，安全撤销对尚未执行动作当前生效；缓存/索引同步失效。",
 "包安装不能替代私人账号授权，不让Agent修改平台控制层。"],[
 "未经校验配置/包不能激活，回滚产生新修订而不是抹去历史。",
 "旧在途调用遵守撤销，平台秘密不进prompt或执行目录。",
 "新版本可评测/禁用，失败发布不破坏上一可用版本。"],
 ["src/uaw/api/","capabilities/","tests/integration/extensions/"],["配置/包发布与回滚演示"])
r("P4-07","workspace","多语言环境、进程回收与可选云后端","增加真实环境能力并保持安装和执行范围受控。","P4-06 P3-05","workspace.environment workspace.process workspace.isolation",[
 "实现管理员批准的Python/Go环境模板，预装优先，按需安装受来源/网络/权限限制。",
 "环境状态以实际版本和检查回执为准，失败保留日志，不假ready。",
 "管理后台进程、初始化失败、租约、资源回收和成果保留，禁止清理项目根。",
 "如D09选择云执行，再接一个真实CloudBackend并报告实际隔离能力；未选则保持关闭。"],[
 "实际执行Python检查与go test样例，缺依赖/安装拒绝/初始化失败正确报告。",
 "释放工作区先处理后台进程，所需成果与用户文件保留。",
 "本地和可选云适配器保留真实安全差异，未配置云不冒充实现。"],
 ["src/uaw/workspace/backends/","apps/local_runner/uaw_runner/","tests/fixtures/environments/"],["模板与支持能力矩阵","真实语言检查与回收报告"],decisions=["D09"])
r("P4-08","model","明确Auto授权与能力恢复","固定模型仍不变，Auto只能在用户授权范围内选择。","P4-06 P3-08","model.policy model.capability model.catalog model.recovery model.usage agent.definitions.model_intent",[
 "实现用户明确选择Auto的政策，记录授权模型集合和适用范围。",
 "按必要协议、上下文、角色上限和预算收窄候选；能力不符不能偷偷覆盖固定模型。",
 "兼容恢复仅在同固定模型或Auto授权内，缺省子Agent继续继承。",
 "记录实际选择理由/配置/usage；未覆盖的阶段授权先补契约，不推断无限授权。"],[
 "explicit根/子/评审都不暗换模型，未授权Auto拒绝。",
 "候选失效或协议不支持反馈当前LLM/用户，而非默认廉价替代。",
 "Auto对照有质量/总成本证据，账单和缓存价格版本可核验。"],
 ["tests/integration/model_policy/","tests/evaluation/model_selection/"],["模型政策/恢复矩阵","Auto授权与对照报告"])
r("P4-09","product","草稿提示、用户控制与完整管理页面","完成实际能力的可理解交互，区分用户和管理员。","P4-01 P4-07 P4-08","ui ingress intent.preview run.approval",[
 "接草稿preview的debounce/取消/版本/有效期，浅色提示随内容伸缩，原文仍是基准。",
 "完善记忆读写开关、连接撤销、模型继承、局部审阅、引用跳转和任务控制。",
 "按D07接辅助/自动审批，拒绝/范围/有效期说明清楚，保留manual。",
 "接管理端配置/包/提供方状态页面；有趣状态文案从真实事件映射，详细动画后续单独设计。"],[
 "旧草稿理解不显示为新草稿，失败不阻止发送或改写原文。",
 "普通用户不接触平台API配置/秘密，审批模式不会扩大范围。",
 "真实状态/缺口/需用户动作清楚可见，细节可展开而非塞满聊天。"],
 ["apps/web/src/features/workspace/","apps/web/src/features/approvals/","apps/web/src/features/references/","apps/web/src/features/admin/"],["实际用户控制与管理页面"],decisions=["D07"])
r("P4-10","foundation","能力增强与撤销一致性验收","验证效率增强不复活过期权限或影响成果质量。","P4-09","",[
 "联测记忆删除、连接撤销、旗标关闭、配置更替、文件修改和旧Context/缓存。",
 "比较长任务压缩、工具检索、结果缓存及Auto在同样材料上的质量/耗费。",
 "明确各能力支持状态、产品开关默认值及没有配置的后端。",
 "未通过关键撤销或引用核验的能力保持关闭并回责任轮修复。"],[
 "撤销后的所有派生路径拒绝旧资源，真实成本统计覆盖全部attempt。",
 "长任务关键要求/引用保留，工具规模增大没有降低权限边界。",
 "有P4报告和可追溯配置，云后端未选时明确not_implemented而非passed。"],
 ["tests/integration/scenarios/","tests/evaluation/","docs/implementation/"],["P4一致性与效率报告"])

r("P5-01","run","跨域检查点与一致提交边界","保存可核验的续跑位置和未决动作。","P4-10","run.checkpoint run.events run.state run.budget",[
 "固定Run/Agent/Plan/Board/Context/Workspace/模型政策/预算的已提交引用。",
 "对齐committed_event_seq与Outbox，未决调用/效果不作为成功结果。",
 "版本化Checkpoint格式，记录实际ReleaseManifest和必要迁移信息。",
 "允许没有TaskGraph或Workspace的简单任务使用相应缺省域，而不是伪造空实体。"],[
 "检查点不引用未提交域版本，缺必要域拒绝发布。",
 "故障边界重读可以找到原始输入和未决动作。",
 "Checkpoint只引用原所有者数据，不成为可独立改业务状态的新仓储。"],
 ["tests/integration/checkpoint/"],["一致检查点样例与故障注入报告"])
r("P5-02","run","租约、当前权限与安全续跑","恢复未完工作而不重复未知外部写。","P5-01","run.resume run.resume.lease run.resume.versions run.resume.access run.resume.effects run.resume.workspace run.resume.continue tool.effects run.cancel",[
 "先取得ExecutionLease/fencing，校验协议兼容及必要迁移。",
 "按当前主体/配置重建访问，Tool对账未决效果，Workspace检查实际文件/环境。",
 "只续跑满足前置条件节点；重复worker/过期租约不能再提交。",
 "区分事件replay、执行resume与新Run rerun，不能承诺联网/模型结果完全复现。"],[
 "网络超时后实际已成功的写不再次派发，无法查询时如实等待/受阻。",
 "撤销权限、丢失设备、变更用户文件、旧模型下线阻止不安全续跑。",
 "重复恢复请求只领取一次，事件续接不重复显示或追加结果。"],
 ["tests/integration/recovery/","apps/local_runner/uaw_runner/"],["恢复/回放/重跑演示与反例"])
r("P5-03","support","完整观测、版本评测与发布候选","用真实结果和成本决定版本是否可试用。","P5-02 P3-08","support.observability support.evaluation support.configuration",[
 "完善脱敏trace、调用/attempt/版本串联和权限受控查询。",
 "固定原始材料、初态、环境、grader和候选/基线ReleaseManifest。",
 "统计可接受成果、包括失败/重试/检查/返工的净时间与成本。",
 "形成发布候选、回归清单、迁移/回滚材料及能力开关清单。"],[
 "可定位哪一模块/版本/尝试导致失败，不依赖私密思维链日志。",
 "每个可接受成果成本含全部尝试；比较阈值测试前固定。",
 "未配置提供方/未实现后端/关闭能力都有真实状态，没有接口覆盖冒充实现。"],
 ["tests/evaluation/","ops/","docs/implementation/"],["版本评测和ReleaseManifest","发布候选资料"])
r("P5-04","agent","handoff与定时扩展实现","完善已规划扩展，但独立UAW首个试用默认关闭。","P5-02 P3-04","agent.collaboration.handoff run.trigger",[
 "实现Agent ControlLease显式移交，原控制者丢失栅栏后不能继续提交。",
 "实现TriggerSpec、时区/occurrence_key、queue/skip/parallel和原权限内预算。",
 "触发新Run与节点Scheduler分开，后台通知按明确用户授权和有意义变化处理。",
 "dev fixture可启用验收，产品handoff/automations默认关闭；D09决定后续启用范围。"],[
 "控制权同时只有一个持有者，移交不携带未确认效果当成功。",
 "重复触发不重复创建Run，定时没有增加权限或换模型。",
 "关闭旗标后调用/恢复也拒绝；缺启用需求不阻塞P5-05试用准备。"],
 ["tests/integration/handoff/","tests/integration/triggers/"],["扩展实现/默认关闭记录"],scope="target_implementation_default_disabled",decisions=["D09"])
r("P5-05","product","单用户工作区受控试用准备","把可用能力交给真实用户，保留账号和设备边界。","P5-03 P4-09","ingress ui workspace.binding support.configuration",[
 "接真实账号会话认证、设备长连接与断线续接，复核部署存储/秘密/访问策略。",
 "完善用户登录/退出、项目/成果/版本导航和可见失败恢复入口。",
 "准备部署、备份/清理、配额及诊断步骤，限定首批单用户工作区范围。",
 "生成可审阅试用发布资料；实际对外部署/发布按届时用户明确授权执行。"],[
 "未认证及越权请求失败，用户资源不跨账号读取，仍不引入团队协作。",
 "真实用户能完成三类样例并纠正/停止/审阅，掉线与设备撤销可解释。",
 "试用包有实际验收证据与回滚步骤，未经授权没有对外发布动作。"],
 ["src/uaw/api/","apps/web/","apps/local_runner/","ops/"],["受控试用发布资料与用户使用说明"],decisions=["D01","D02"])
r("P5-06","integration","推特入口适配设计预留","UAW独立完成后再确定如何包装到推特。","P5-03","",[
 "按D10明确请求渠道或社媒产品的范围，仅规划入口/身份/成果反馈适配。",
 "列出能力开关、平台账号授权及外部发布审批映射，不改变核心Agent循环。",
 "把代码/本地访问等不适用能力在产品配置关闭，仍保留UAW核心实现。",
 "后续业务需求确认后另拆实现轮；本轮不承诺内容日历、自动发布或运营策略已实现。"],[
 "适配边界和未确认需求写清，固定推特策略没有进入通用Runtime。",
 "推特权限不会扩展UAW或反向修改其用户模型政策。",
 "本轮只有适配设计，独立UAW发布不依赖此轮完成。"],
 ["extensions/twitter/","docs/integrations/"],["推特适配候选设计与旗标映射"],status="deferred",scope="future_adapter_design_only",decisions=["D10"])
r("P5-07","foundation","交付盘点与开发移交","把实际完成、未完成和默认关闭能力分别列清。","P5-05","",[
 "逐节点/接口对照实际代码、验收报告和配置，更新实现证据而不只改布尔值。",
 "整理运行/部署/恢复/管理员/用户说明及已知问题。",
 "区分核心试用范围、已实现默认关闭扩展、未选云后端和后续推特需求。",
 "形成下一批改进任务；未完成轮不能因为时间/预算耗尽标完成。"],[
 "核心闭环和三个工作场景有可复查证据。",
 "没有以文档、mock或隐藏旗标冒充实现。",
 "主索引、接口、设计、代码和实际报告一致，下一轮可从明确未过项接续。"],
 ["docs/implementation/","ops/"],["阶段交付清单与后续任务表"])

# Actual progress is kept separately from the planned tasks and backed by recorded evidence.
IMPLEMENTATION_STATUS = {
    "P1-02": dict(status="in_progress", implementation_evidence=[
        "docs/implementation/MS-I1.md", "docs/implementation/MS-C2-acceptance.md",
        "docs/implementation/MS-I2b.md", "docs/implementation/MS-I2c.md",
        "docs/implementation/evidence/environment.json",
        "docs/implementation/evidence/p0-tests.xml",
    ]),
    "P1-03": dict(status="in_progress", implementation_evidence=[
        "docs/implementation/MS-I1.md", "docs/implementation/MS-I2a.md", "docs/implementation/MS-I2b.md", "docs/implementation/MS-I2c.md", "docs/implementation/evidence/environment.json",
        "docs/implementation/evidence/p0-tests.xml",
    ]),
    "P1-04": dict(status="in_progress", implementation_evidence=[
        "docs/implementation/MS-I1.md", "docs/implementation/MS-I2a.md", "docs/implementation/MS-I2b.md", "docs/implementation/MS-I2c.md", "docs/implementation/evidence/environment.json",
        "docs/implementation/evidence/p0-tests.xml",
    ]),
    "P1-01": dict(status="in_progress", implementation_evidence=[
        "docs/implementation/P1-01.md",
        "docs/implementation/evidence/environment.json", "docs/implementation/evidence/p0-tests.xml",
    ]),
    "P0-05": dict(status="in_progress", implementation_evidence=[
        "docs/implementation/P0-05.md", "docs/implementation/evidence/environment.json",
        "docs/implementation/evidence/p0-tests.xml",
    ]),
    "P0-03": dict(status="accepted", implementation_evidence=[
        "docs/implementation/P0-03.md", "docs/implementation/evidence/environment.json",
        "docs/implementation/evidence/p0-tests.xml",
    ]),
    "P0-04": dict(status="accepted", implementation_evidence=[
        "docs/implementation/P0-04.md", "docs/implementation/evidence/environment.json",
        "docs/implementation/evidence/p0-tests.xml",
    ]),
    "P0-01": dict(status="accepted", implementation_evidence=[
        "docs/implementation/P0-01.md", "docs/implementation/evidence/environment.json",
        "docs/implementation/evidence/p0-tests.xml",
    ]),
    "P0-02": dict(status="in_progress", implementation_evidence=[
        "docs/implementation/P0-02.md", "docs/implementation/evidence/environment.json",
        "docs/implementation/evidence/p0-tests.xml",
    ]),
}
for work_package in ROUNDS:
    if work_package["id"] in IMPLEMENTATION_STATUS:
        work_package.update(IMPLEMENTATION_STATUS[work_package["id"]])
