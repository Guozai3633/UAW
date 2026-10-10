"""UAW authored wire contracts. This module defines specs, not backend handlers."""
import copy

TYPES = {}
OWNERS = {}
RULES = {}
OPERATIONS = []


def ref(name):
    return {"$ref": "#/$defs/" + name}


def arr(name, maximum=256, minimum=0):
    return {"type": "array", "items": ref(name), "minItems": minimum, "maxItems": maximum}


def nullable(schema):
    return {"anyOf": [copy.deepcopy(schema), {"type": "null"}]}


def field(kind, description, optional=False, default=None, **constraints):
    schema = ref(kind) if isinstance(kind, str) else copy.deepcopy(kind)
    schema.update(description=description, **constraints)
    if default is not None:
        schema["default"] = default
    return (schema, not optional)


def obj(name, owner, description, fields, rules=()):
    assert name not in TYPES, name
    TYPES[name] = {"type": "object", "description": description, "properties": {k: v[0] for k, v in fields.items()},
                   "required": [k for k, v in fields.items() if v[1]], "additionalProperties": False}
    OWNERS[name] = owner
    RULES[name] = list(rules)
    return name


def scalar(name, owner, description, **schema):
    assert name not in TYPES, name
    TYPES[name] = dict(description=description, **schema)
    OWNERS[name] = owner
    RULES[name] = []


def enum(name, values, owner="common"):
    scalar(name, owner, "取值含义见字段及协议约束。", type="string", enum=values.split("|"))


def alias(name, target):
    scalar(name, OWNERS[target], "命名兼容别名，结构以 " + target + " 为准。", **ref(target))


scalar("ID", "common", "域内不透明标识，不能推断主体或访问权限。", type="string", minLength=1, maxLength=128, pattern=r"^[A-Za-z0-9][A-Za-z0-9._:-]*$")
scalar("Text", "common", "普通短文本；大正文使用Blob/Ref，限额为实验默认可配置。", type="string", maxLength=16384)
scalar("NonEmptyText", "common", "非空业务文本。", type="string", minLength=1, maxLength=16384)
scalar("Timestamp", "common", "UTC RFC3339时间；实现必须校验时间与时钟偏差。", type="string", format="date-time")
scalar("Version", "common", "不可变内容/协议版本，不可用显示名替代。", type="string", minLength=1, maxLength=128)
scalar("Revision", "common", "CAS单调修订号；0仅表示对象尚不存在，已有版本从1开始。", type="integer", minimum=0)
scalar("Count", "common", "非负计数。", type="integer", minimum=0, maximum=2147483647)
scalar("Duration", "common", "毫秒；0仅在明确支持非阻塞查询的接口允许。", type="integer", minimum=0, maximum=604800000)
scalar("Hash", "common", "SHA-256内容/规范参数摘要；不是匿名化。", type="string", pattern="^[a-f0-9]{64}$")
scalar("Cursor", "common", "不透明分页/事件位置；主体与过滤范围绑定，过期需快照。", type="string", minLength=1, maxLength=2048)
scalar("Decimal", "common", "精确非负十进制字符串，用于金额，不以二进制float计账。", type="string", pattern=r"^(0|[1-9][0-9]*)(\.[0-9]{1,9})?$")
scalar("URL", "common", "绝对HTTP(S)候选地址；网络策略必须独立检查重定向/地址。", type="string", format="uri", maxLength=4096, pattern="^https?://")
scalar("RelativePath", "workspace", "项目内相对路径；机器还须解析真实路径/链接并核验授权根。", type="string", minLength=1, maxLength=1024,
       pattern=r"^(?![/\\]|[A-Za-z]:)(?!.*(?:^|[/\\])\.\.(?:[/\\]|$)).+$")
scalar("Path", "workspace", "仅用户目录选择/Runner可信协议允许的原生路径；不可直接交模型授予访问。", type="string", minLength=1, maxLength=4096)
scalar("Bool", "common", "布尔值，不能用字符串true或整数替代。", type="boolean")
scalar("JsonValue", "common", "仅用于显式扩展载荷/工具动态参数；必须再按关联schema验证，非可信权限。",
       oneOf=[{"type": "null"}, {"type": "boolean"}, {"type": "number"}, {"type": "string"},
              {"type": "array", "items": ref("JsonValue")}, {"type": "object", "additionalProperties": ref("JsonValue")}])
scalar("Object", "common", "动态工具参数或注册扩展配置；必须有具体ToolSpec/config schema约束。", type="object", additionalProperties=ref("JsonValue"))
scalar("Schema", "tool", "JSON Schema 2020-12注册片段；不得联网任意解析远端$ref，须可信注册/资源上限。", type="object", additionalProperties=ref("JsonValue"))

for name, values in {
 "Purpose":"draft_preview|understanding|agent_step|subagent_handoff|tool_result|plan_revision|semantic_compression|context_pruning|final_synthesis",
 "Outcome":"succeeded|partial|blocked|failed|cancelled", "EffectState":"confirmed|pending|unknown",
 "RunStatus":"queued|preparing|running|verifying|waiting_for_user|waiting_for_merge|completed|failed|cancelled",
 "State":"pending|ready|running|waiting|completed|failed|stale|cancelled",
 "Impact":"low|medium|high", "DeliveryDecision":"accept|reject|revise|partial_accept",
 "ControlMode":"steer|enqueue|replace|cancel|deliver_partial", "ApprovalMode":"assisted|manual|automatic",
 "ApprovalDecisionKind":"approve_once|approve_scoped|decline|cancel", "CheckState":"passed|failed|not_run|blocked",
 "ModelMode":"inherit|explicit|auto", "PlanningLevel":"none|steps|dag", "DelegationMode":"single|parent_child",
 "Parallelism":"serial|parallel", "ProviderState":"draft|validated|active|disabled|revoked",
 "ConnectionState":"disconnected|connecting|active|expired|revoked|error",
 "RefKind":"web|asset|content|artifact|workspace|verification|local|input|task|task_frame|semantic_parse|plan|agent_definition|agent_instance|skill|memory|context|tool_call|policy|environment|process|configuration|checkpoint|usage|trace|evaluation|review|changeset",
 "ItemType":"user_message|understanding|agent_message|plan|tool_call|command|file_change|approval|user_control|artifact|review|context_compression",
 "ItemStatus":"pending|in_progress|waiting|completed|failed|declined|cancelled",
 "FailureCategory":"arguments|authorization|policy|dependency|conflict|model_protocol|tool_business|infrastructure|budget|timeout|cancelled|unknown_effect",
 "MessageRole":"system|developer|user|assistant|tool",
}.items(): enum(name, values)

obj("Scope", "common", "资源域选择器，不是授权凭证。", {
 "principal_id":field("ID","有效主体，由可信通道提供"), "conversation_id":field("ID","会话范围",True),
 "task_id":field("ID","任务范围",True), "project_id":field("ID","已绑定项目范围",True),
 "resource_refs":field(arr("Ref",128),"进一步收窄资源",True), "capabilities":field(arr("NonEmptyText",128),"请求/有效能力标签，服务端求交集",True),
}, ["客户端scope只能作为请求选择器，不能覆盖可信scope；单用户也验证对象归属。"])
obj("Principal", "common", "可信身份摘要，不包含凭据。", {
 "id":field("ID","身份ID"), "kind":field({"type":"string","enum":["user","admin","service","runner"]},"身份类别"),
 "auth_session_id":field("ID","已认证会话/设备绑定"), "delegated_by":field("ID","委托来源",True),
})
obj("Location", "context", "引用定位器，kind对应字段由Runtime交叉检查。", {
 "kind":field({"type":"string","enum":["whole","page","lines","paragraph","json_pointer","cell_range","text_span"]},"定位种类"),
 "start":field("Count","起点：页/行从1，字符offset从0",True), "end":field("Count","含义随kind，字符end为排他",True),
 "anchor":field("Text","段落ID/JSON Pointer/单元格范围",True), "relative_path":field("RelativePath","工作区内文件位置",True),
}, ["end不得小于start；whole不填写起止；page/lines必须start>=1；json_pointer/cell_range必须anchor。"])
obj("Ref", "common", "跨域资源引用；资源本体/权限归所属领域。", {
 "kind":field("RefKind","来源类型"),"id":field("ID","资源ID"),"version":field("Version","实际来源版本"),
 "location":field("Location","可选定位",True),"content_hash":field("Hash","取得内容摘要",True),
 "access_scope":field("Scope","可见范围，由来源域确认",True),
}, ["引用可解析不表示当前有权限；删除/撤销不能通过旧Ref读取。"])
alias("PathRef","Ref")
obj("RequestMeta", "common", "所有服务端操作的关联与幂等元数据。", {
 "request_id":field("ID","同逻辑请求重试不变"),"schema_version":field("Version","契约版本"),
 "expected_revision":field(nullable(ref("Revision")),"修改时的CAS版本，创建可为0",True),
})
obj("Failure", "common", "类型化失败，不携带秘密与隐藏思维。", {
 "code":field("ID","稳定错误码"),"category":field("FailureCategory","错误类别"),"message":field("Text","用户可见安全说明"),
 "retryable":field("Bool","是否允许按原契约恢复"),"failed_phase":field("NonEmptyText","失败阶段"),
 "recover_hint":field("Text","可允许的修复建议",True),"evidence_refs":field(arr("Ref"),"受控诊断证据",True),
 "side_effect_state":field("EffectState","实际副作用状态",True),"retry_after_ms":field("Duration","可选退避",True),
})
obj("ResourceVector", "run", "多维资源额度/估计/已用量；字段单位不混用。", {
 "input_tokens":field("Count","输入token"),"output_tokens":field("Count","输出token"),"model_calls":field("Count","模型调用"),
 "tool_calls":field("Count","工具调用"),"child_agents":field("Count","子实例数"),"wall_time_ms":field("Duration","任务墙钟时间"),
 "money":field("Decimal","金额"),"currency":field({"type":"string","pattern":"^[A-Z]{3}$"},"币种"),
})
obj("Budget", "run", "运行总预算/子预算请求。", {
 "limits":field("ResourceVector","总上限"),"max_steps":field("Count","动作循环次数上限"),
 "max_depth":field("Count","委派最大深度"),"deadline":field("Timestamp","绝对截止"),"parent_reservation_ref":field("Ref","父预留引用",True),
}, ["实际执行上限必须正值且不高于父预算/平台政策；未知费用待对账，不记零。"])
obj("Usage", "model", "一次attempt实际或待核对用量。", {
 "attempt_id":field("ID","真实尝试ID"),"resources":field("ResourceVector","已知用量"),
 "billing_state":field({"type":"string","enum":["confirmed","estimated","pending"]},"账单确定程度"),
 "provider_receipt_id":field("ID","去重账单回执",True),"cached_input_tokens":field("Count","供应商实际报告缓存输入",True),
})
obj("TrustedExecutionContext", "common", "服务端/Runner注入，不属于模型/HTTP请求体。", {
 "principal":field("Principal","可信主体"),"scope":field("Scope","当前有效范围"),"operation_id":field("ID","操作关联"),
 "conversation_id":field("ID","会话",True),"task_id":field("ID","任务",True),"run_id":field("ID","Run；正式执行必需",True),
 "agent_id":field("ID","实例",True),"node_id":field("ID","节点",True),"trace_id":field("ID","诊断关联"),
 "attempt_id":field("ID","执行尝试"),"deadline":field("Timestamp","剩余时间据此计算"),
 "model_policy_ref":field("Ref","有效模型政策",True),"capability_policy_ref":field("Ref","有效能力政策"),
 "budget_reservation_ref":field("Ref","已预留预算",True),
})
obj("ToolRuntimeContext", "tool", "可信调用上下文扩展，非模型ContextSnapshot。", {
 "execution":field("TrustedExecutionContext","可信执行关联"),"action_id":field("ID","逻辑动作"),
 "approval_ref":field("Ref","Run当前审批依据",True),"business_key":field("NonEmptyText","稳定外部业务幂等键",True),
})
obj("PageRequest", "common", "稳定过滤条件下分页。", {"cursor":field("Cursor","续页",True),"limit":field({"type":"integer","minimum":1,"maximum":100},"页大小",True,20)})
obj("Acknowledgement", "common", "确认受理，不证明整个任务已完成。", {"operation_id":field("ID","受理ID"),"status":field({"type":"string","enum":["accepted","unchanged","completed","pending"]},"确认状态"),"related_refs":field(arr("Ref"),"相关资源",True)})
obj("Requirement", "agent", "用户/政策验收要求。", {"id":field("ID","要求ID"),"text":field("NonEmptyText","语义内容"),"mandatory":field("Bool","是否必需"),"source_refs":field(arr("Ref",64,1),"用户或政策来源"),"evidence_kinds":field(arr("NonEmptyText",32),"可接受证据类别",True)})
alias("Constraint","Requirement")
obj("OutputSpec", "agent", "一个可交付结果要求。", {"id":field("ID","成果要求ID"),"kind":field("NonEmptyText","成果类型"),"description":field("NonEmptyText","内容/用途"),"required":field("Bool","必需"),"schema_ref":field("Ref","结构检查schema",True)})
obj("Contract", "agent", "语义目标+结构+证据契约，不写死行业字段。", {"goal":field("NonEmptyText","目标"),"requirements":field(arr("Requirement",128),"验收条件"),"outputs":field(arr("OutputSpec",32),"交付物要求"),"version":field("Version","契约版本"),"acceptance_required":field("Bool","Task结束是否需用户接受",True,False)})
alias("DeliveryContract","Contract")
obj("ModelRequest", "model", "用户模型意图，尚未解析为实际模型配置。", {"mode":field("ModelMode","inherit/explicit/auto"),"requested_name":field("NonEmptyText","explicit时用户原指定名",True),"source_input_ref":field("Ref","明确覆盖/Auto授权来源",True),"allowed_model_ids":field(arr("ID",64),"Auto授权范围",True)}, ["inherit不得填requested_name；explicit必需requested_name和用户来源；auto须有效授权且无静默扩范围。"])
TYPES["ModelRequest"]["allOf"] = [
 {"if":{"properties":{"mode":{"const":"explicit"}},"required":["mode"]},"then":{"required":["requested_name","source_input_ref"]}},
 {"if":{"properties":{"mode":{"const":"inherit"}},"required":["mode"]},"then":{"not":{"required":["requested_name"]}}},
 {"if":{"properties":{"mode":{"const":"auto"}},"required":["mode"]},"then":{"required":["source_input_ref"]}},
]
alias("ModelSelection","ModelRequest")
obj("AgentDefinitionDraft", "agent", "用户要求持久保存的角色草案。", {
 "client_definition_key":field("ID","批量每项稳定幂等键"),"name":field({"type":"string","minLength":1,"maxLength":80},"会话内唯一名称"),
 "description":field("NonEmptyText","短职责"),"instructions":field("NonEmptyText","短工作指令"),
 "use_when":field(arr("NonEmptyText",32,1),"语义调用条件"),"avoid_when":field(arr("NonEmptyText",32),"排除条件"),
 "skill_refs":field(arr("Ref",32),"获准技能依赖"),"tool_categories":field(arr("ID",64),"能力类别请求"),
 "input_contract":field("Contract","必要输入及缺口语义"),"output_contract":field("Contract","子结果验收"),
 "model_request":field("ModelRequest","模型意图，默认显式填写inherit"),
}, ["不含owner/conversation/approved；服务注入，角色不能授予新权限；临时分工不得自动持久保存。"])
alias("Draft","AgentDefinitionDraft")
obj("AgentDefinitionVersion", "agent", "已提交角色版本。", {"definition_id":field("ID","定义ID"),"revision":field("Revision","单调版本"),"content_hash":field("Hash","不可变摘要"),"owner_id":field("ID","真实用户"),"conversation_id":field("ID","绑定会话"),"draft":field("AgentDefinitionDraft","保存配置"),"status":field({"type":"string","enum":["enabled","disabled","pending_resolution"]},"可调用状态"),"source_input_ref":field("Ref","用户来源"),"created_at":field("Timestamp","提交时间")})
obj("AgentCandidate", "agent", "可见角色摘要，不加载全部方法。", {"definition_ref":field("Ref","固定版本"),"name":field("NonEmptyText","名称"),"description":field("NonEmptyText","职责"),"use_when":field(arr("NonEmptyText",32),"调用条件"),"avoid_when":field(arr("NonEmptyText",32),"排除"),"available":field("Bool","当前可用摘要，调用仍复核"),"output_contract_ref":field("Ref","验收契约")})
obj("DefinitionItemResult", "agent", "批量创建/更新的逐项结果。", {"client_definition_key":field("ID","输入项关联"),"status":field({"type":"string","enum":["created","updated","unchanged","needs_resolution","failed"]},"单项结果"),"definition":field("AgentDefinitionVersion","成功配置",True),"failure":field("Failure","阻碍项",True)}, ["成功须definition，failed/needs_resolution须failure；atomic失败不能仍返回created。"])
obj("DefinitionBatchResult", "agent", "批量元数据提交结果。", {"batch_policy":field({"type":"string","enum":["atomic","independent"]},"提交策略"),"items":field(arr("DefinitionItemResult",16,1),"逐项真实结果"),"committed_revision":field("Revision","已提交域修订",True)})
obj("DefinitionPatch", "agent", "可修改配置的白名单字段，省略表示不变，null不默认删除。", {k: (v[0],False) for k,v in {"name":field("NonEmptyText","新名"),"description":field("NonEmptyText","新职责"),"instructions":field("NonEmptyText","新方法"),"use_when":field(arr("NonEmptyText",32),"新条件"),"avoid_when":field(arr("NonEmptyText",32),"新排除"),"skill_refs":field(arr("Ref",32),"替换技能列表"),"tool_categories":field(arr("ID",64),"新能力请求"),"output_contract":field("Contract","新验收"),"model_request":field("ModelRequest","用户明确模型修订"),"enabled":field("Bool","启停")}.items()}, ["至少一个字段；模型/权限变动须有效用户来源；CAS提交。"])
TYPES["DefinitionPatch"]["minProperties"]=1

# Domain structures. `?` means absent is allowed, never implicit null.
def record(name, owner, description, spec, rules=()):
    fields={}
    for line in spec.strip().splitlines():
        key, kind, note=line.split("|",2)
        optional=key.endswith("?"); key=key.rstrip("?")
        schema=arr(kind[3:-1]) if kind.startswith("[](") else ref(kind)
        fields[key]=field(schema,note,optional)
    return obj(name,owner,description,fields,rules)

record("ScopeSelector","common","客户端请求缩小可读范围，不能自行指定主体或授予能力。", """
conversation_id?|ID|会话筛选
task_id?|ID|任务筛选
project_id?|ID|项目筛选
resource_refs?|[](Ref)|指定材料
""",["服务端将选择器与当前主体有效权限求交；不得跨账号引用。"])
record("Interpretation","intent","一个有来源的理解候选。", """
goal|NonEmptyText|候选目标
assumptions|[](NonEmptyText)|未获用户确认的假设
source_refs|[](Ref)|原文与补充来源
missing_facts|[](NonEmptyText)|缺少的信息
""")
record("TaskFrame","intent","版本化任务理解。原文保持独立，理解不能覆盖原文。", """
task_id|ID|关联任务
revision|Revision|当前理解版本
original_input_ref|Ref|原始用户输入
patch_refs|[](Ref)|运行中追加要求
goal|NonEmptyText|理解目标
constraints|[](Constraint)|约束及来源
output_specs|[](OutputSpec)|成果要求
assumptions|[](NonEmptyText)|明确标记的假设
unresolved|[](NonEmptyText)|未解问题
evidence_refs|[](Ref)|已读取材料
created_at|Timestamp|版本提交时间
""")
TYPES["TaskFrame"]["properties"]["summary"] = dict(ref("NonEmptyText"), description="AI理解的提示摘要，不授权动作、不替代完整原文。")
TYPES["TaskFrame"]["properties"]["goal"] = {"type":"string","minLength":1,"maxLength":131072,"description":"本轮以完整原文及追加要求作为任务基准；AI摘要单独放summary。"}
TYPES["TaskFrame"]["properties"]["input_revision"] = dict(ref("Revision"), description="生成时的Run输入集合版本；旧理解不得覆盖新输入。")
TYPES["TaskFrame"]["properties"]["semantic_parse_ref"] = dict(ref("Ref"), description="有界模型提案及来源位置，保留模型回执。")
record("RunInputState","run","Run拥有的用户输入集合；追加要求只经真实用户入口保存。","run_id|ID|运行\nconversation_id|ID|会话\nrevision|Revision|输入集合版本\noriginal_input_ref|Ref|不可变原文\npatch_refs|[](Ref)|按顺序追加的用户要求")
record("IntentQuote","intent","逐字引文，坐标是Python/Unicode码点半开区间[start,end)，不是UTF8字节。","source_index|Count|0原文，其余按补充顺序\nstart|Count|起始码点\nend|Count|结束码点\ntext|NonEmptyText|原文逐字片段")
record("IntentRequirementProposal","intent","只提取有逐字来源的要求，不能自授权限。","quote|IntentQuote|来源位置")
record("IntentOutputProposal","intent","成果类型是描述，不是能力授权；描述必须逐字引用用户输入。","kind|NonEmptyText|通用成果描述\nquote|IntentQuote|用户成果要求原文")
record("IntentProposal","intent","LLM提案；summary仅提示，推断与缺口必须独立列出。","summary|NonEmptyText|AI理解摘要\nrequirements|[](IntentRequirementProposal)|有来源约束\noutputs|[](IntentOutputProposal)|有来源成果\nassumptions|[](NonEmptyText)|未经确认假设\nunresolved|[](NonEmptyText)|缺口或矛盾")
TYPES["IntentProposal"]["properties"]["summary"]={"type":"string","minLength":1,"maxLength":2000}
for proposal_name, field_name, maximum in [("IntentProposal","requirements",64),("IntentProposal","outputs",16),("IntentProposal","assumptions",32),("IntentProposal","unresolved",32)]:
    TYPES[proposal_name]["properties"][field_name]["maxItems"]=maximum
for text_field in ("assumptions","unresolved"):
    TYPES["IntentProposal"]["properties"][text_field]["items"]={"type":"string","minLength":1,"maxLength":2000}
TYPES["IntentQuote"]["properties"]["text"]={"type":"string","minLength":1,"maxLength":16384}
TYPES["IntentOutputProposal"]["properties"]["kind"]={"type":"string","minLength":1,"maxLength":80}
record("IntentSemanticRecord","intent","已核对逐字来源的模型提案；不证明摘要语义质量已验收。","run_id|ID|运行\ninput_revision|Revision|输入集合版本\nsource_refs|[](Ref)|读取的完整用户输入\nproposal|IntentProposal|候选\nmodel_output_ref|Ref|真实ModelRuntime回执\ncontext_snapshot_ref|Ref|固定模型输入")
record("IntentReceipt","intent","理解提交与事件同事务保存的幂等回执。","request_hash|Hash|请求与可信关联摘要\nrun_id|ID|运行\ninput_revision|Revision|源版本\nframe_ref|Ref|提交版本\nresult|Object|已验证的Runtime结果")
record("IntentFrameBinding","intent","理解版本对应的Run与原始输入集合。","run_id|ID|运行\ninput_revision|Revision|源版本\nsource_refs|[](Ref)|完整来源\nsemantic_parse_ref|Ref|模型提案")
record("IntentContextBinding","context","understanding专用有界快照绑定；不是完整规则继承实现。","run_id|ID|运行\ninput_revision|Revision|输入集合版本\nsource_refs|[](Ref)|原文和补充\ntemplate_hash|Hash|包内固定提示词摘要")
record("ExecutionAssessment","agent","四个独立执行选择，属于可修改建议，不授予权限。", """
planning|PlanningLevel|无规划、清单或依赖图
delegation|DelegationMode|单Agent或父子Agent
parallelism|Parallelism|顺序或独立部分并发
information_state|InformationState|可以开始、先读材料或澄清
rationale|NonEmptyText|判断依据及成本收益
candidate_agent_refs|[](Ref)|可用角色候选
independent_groups|[](WorkGroup)|可独立执行的工作
reassessment_conditions|[](NonEmptyText)|需要重新判断的条件
source_frame_ref|Ref|本次理解版本
""")
enum("InformationState","ready|read_materials|clarify","agent")
record("WorkGroup","agent","独立性是建议，调度器仍检查读写集合。", """
id|ID|工作组
goal|NonEmptyText|分工目标
input_refs|[](Ref)|已知输入
read_refs|[](Ref)|读集
write_refs|[](Ref)|写集
""")
record("NodeSpec","agent","任务图节点，与Agent实例不是一一对应。", """
id|ID|图内稳定ID
goal|NonEmptyText|节点目标
depends_on|[](ID)|前置节点ID
input_refs|[](Ref)|固定输入
output_contract|Contract|节点交付标准
agent_definition_ref?|Ref|可选指定角色
read_refs|[](Ref)|预计读集
write_refs|[](Ref)|预计写集
budget|Budget|节点预算上限
""",["依赖必须存在、无自环、无环；并发写必须隔离或串行；图节点不自动创建子Agent。"])
record("PlanPatch","agent","替换受影响节点并传播失效。", """
base_revision|Revision|目标图版本
upsert_nodes|[](NodeSpec)|新增或替换节点
remove_node_ids|[](ID)|移除节点
reason|NonEmptyText|变更理由
source_input_ref?|Ref|用户修订依据
""",["已发生的外部动作不能随计划删除而抹除；运行节点先取消/对账再迁移。"])
record("TaskGraph","agent","图修订不可变，执行状态另存。", """
task_id|ID|所属任务
revision|Revision|计划版本
planning|PlanningLevel|steps或dag；none没有图
nodes|[](NodeSpec)|完整节点集合
source_frame_ref|Ref|目标理解版本
created_at|Timestamp|提交时间
""")
record("NodeState","agent","节点状态与依赖版本。", """
node_id|ID|节点
plan_revision|Revision|所属图
state|State|执行状态
input_refs|[](Ref)|实际输入
result_refs|[](Ref)|结果引用
agent_instance_ref?|Ref|执行实例
failure?|Failure|失败详情
""")
record("ResourceSnapshot","agent","当前可调度容量，不代表已预留。", """
revision|Revision|资源账本版本
available|ResourceVector|剩余资源
active_leases|[](Ref)|占用控制/工作区租约
""")
record("DelegationSpec","agent","一次有界委派；独立上下文，不共享可变提示词。", """
goal|NonEmptyText|当前委派目标
input_refs|[](Ref)|授权输入
definition_ref?|Ref|固定角色版本
output_contract|Contract|子成果验收标准
budget|Budget|父预算内切分
read_refs|[](Ref)|允许读取范围请求
write_refs|[](Ref)|允许修改范围请求
creation_key|ID|委派幂等键
""",["定义权限、父权限、产品旗标、设备权限求交；父预算必须先预留；默认继承父模型。"])
record("RoleProfile","agent","平台角色能力上限，可与用户子Agent定义组合。", """
id|ID|角色ID
version|Version|不可变版本
description|NonEmptyText|职责
instructions_ref|Ref|方法来源
tool_categories|[](ID)|工具类别上限
skill_refs|[](Ref)|技能候选
output_contract|Contract|角色验收
""")
record("AgentInstance","agent","运行实例与持久定义分离。", """
id|ID|实例ID
run_id|ID|所属运行
parent_agent_ref?|Ref|根实例无父
definition_ref?|Ref|使用的角色版本
delegation_ref?|Ref|子实例的委派契约
status|State|实例状态
model_policy_ref|Ref|实际继承或覆盖政策
capability_policy_ref|Ref|有效权限交集
context_epoch|Revision|上下文纪元
workspace_ref?|Ref|需要文件操作时绑定
result_ref?|Ref|终态结果
revision|Revision|实例版本
""")
record("AgentResult","agent","子Agent返回候选成果，父Agent仍需核验。", """
agent_ref|Ref|完成实例版本
outcome|Outcome|真实结果
summary|Text|结果摘要
output_refs|[](Ref)|交付引用
verification_refs|[](Ref)|核验证据
limitations|[](NonEmptyText)|未完成项
usage_ref|Ref|真实累计用量
""")
record("AgentMessage","agent","协作通道只传授权引用和短消息。", """
message_id|ID|通道去重键
from_ref|Ref|发送实例
to_ref|Ref|接收实例
task_revision|Revision|共同任务基线
text|Text|协作内容
payload_refs|[](Ref)|共享资料/候选结果
created_at|Timestamp|提交时间
""")
record("ControlLease","agent","写控制权有期限与栅栏，阻止过期执行者继续提交。", """
id|ID|租约ID
holder_ref|Ref|当前控制实例
resource_ref|Ref|受控任务/节点
fencing_token|Revision|单调栅栏
expires_at|Timestamp|截止时间
revision|Revision|控制域版本
""")
record("BoardEntry","agent","版本化共享结果，不存所有Agent私有思维。", """
key|ID|条目键
result_ref|Ref|候选/确认结果
status|BoardStatus|确认程度
provenance|[](Ref)|证据来源
input_refs|[](Ref)|结果依赖版本
revision|Revision|条目修订
""")
enum("BoardStatus","candidate|confirmed|stale","agent")
record("SkillSpec","agent","方法包只先提供摘要，激活时加载完整指令。", """
id|ID|技能ID
version|Version|版本
name|NonEmptyText|名称
description|NonEmptyText|适用任务
instruction_ref|Ref|完整方法
dependency_refs|[](Ref)|脚本/模板/资料
required_capabilities|[](ID)|能力需求
output_contract|Contract|验收标准
content_hash|Hash|内容摘要
""")
record("TaskTemplate","agent","可复用任务模板允许锁定稳定部分。", """
id|ID|模板
revision|Revision|版本
contract|Contract|目标和验收
source_refs|[](Ref)|材料入口
plan_ref?|Ref|可选固定步骤
skill_refs|[](Ref)|方法
locked_fields|[](NonEmptyText)|禁止自动修改的字段路径
""")
record("DeliveryProposal","agent","候选完成提案，不能由模型直接置Run为completed。", """
run_ref|Ref|目标运行版本
contract_ref|Ref|交付标准
outcome|Outcome|建议终态
artifact_refs|[](Ref)|成果版本
report_ref|Ref|语义及执行证据报告
unresolved_effect_refs|[](Ref)|未确认外部效果
created_at|Timestamp|提案时间
""",["必需要求缺证据、成果过期或未知写效果时不得标记全部成功。"])

# Context, references, memory.
enum("FreshnessPolicy","pinned|latest_required|bounded_age","context")
record("ContextBlock","context","分区、溯源、可裁剪的模型输入块。", """
id|ID|输入块
kind|BlockKind|指令/材料/历史/结果
source_refs|[](Ref)|实际来源
content_ref|Ref|内容
estimated_tokens|Count|估算Token
required|Bool|是否禁止丢弃
trust|TrustLevel|指令可信度
""")
enum("BlockKind","instruction|user_input|history|material|memory|board|tool_result|skill","context")
enum("TrustLevel","platform|user|project|external","context")
record("InstructionRule","context","指令作用域与优先级显式可追溯。", """
id|ID|规则
source_ref|Ref|原始规则
level|InstructionLevel|优先层
scope|ScopeSelector|适用范围
text|NonEmptyText|指令内容
""")
enum("InstructionLevel","platform|capability_policy|user_current|project|user_preference|role|skill","context")
record("InstructionSet","context","已解决作用域的规则集合。", """
rules|[](InstructionRule)|生效指令
conflict_refs|[](Ref)|无法自动消解的冲突
version|Version|固定版本
""")
record("PreservationSpec","context","压缩必须保留的任务与证据集合。", """
required_refs|[](Ref)|不可丢失来源
exact_strings|[](NonEmptyText)|数字、路径等精确文本
requirement_ids|[](ID)|关键约束
pending_action_refs|[](Ref)|未决动作
""")
record("Manifest","context","可检查的派生输入与依赖清单。", """
version|Version|格式版本
input_refs|[](Ref)|输入版本
dependency_refs|[](Ref)|派生依赖
content_hash|Hash|清单摘要
""")
record("ContextSnapshot","context","一次模型调用的不可变输入；引用固定实际内容。", """
id|ID|快照
epoch|Revision|上下文纪元
purpose|Purpose|构建目的
blocks|[](ContextBlock)|按顺序输入
instruction_set_ref|Ref|已解决规则
capability_snapshot_ref|Ref|本轮工具/角色摘要
manifest|Manifest|依赖
input_tokens|Count|估算输入量
output_reserve|Count|保留输出Token
tool_reserve|Count|保留工具往返Token
omitted_refs|[](Ref)|主动裁剪资料
compressed_refs|[](Ref)|语义压缩结果
""",["总预算必须适配实际模型；关键用户要求不可静默裁掉；资料内容不自动升级为指令。"])
record("ReferenceRecord","context","引用登记不等于声称证据支持结论。", """
ref|Ref|稳定引用
title|NonEmptyText|人可读标题
source_url?|URL|获准网页原URL
content_ref|Ref|实际读取的内容
retrieved_at|Timestamp|读取时间
provenance_refs|[](Ref)|来源链
access_scope|Scope|服务端授权范围
""")
record("Citation","context","一句主张到实际资料位置的映射。", """
claim_id|ID|结论锚点
source_ref|Ref|固定版本和位置
support|CitationSupport|支持程度
explanation|Text|推断、冲突或限制
""")
enum("CitationSupport","direct|inference|contradiction|insufficient","context")
record("IngestionRecord","context","资料发布与索引版本必须一致。", """
id|ID|摄取作业
source_ref|Ref|原材料
parser_version|Version|解析器版本
chunk_profile|ID|切分参数
embedding_profile|ID|向量模型/配置
active_revision|Revision|已发布索引
chunk_refs|[](Ref)|发布块
status|State|作业状态
failure?|Failure|失败原因
""")
record("RetrievalHit","context","检索命中携带位置和版本。", """
source_ref|Ref|实际资料
content_ref|Ref|片段内容
score|Score|检索相关性，仅用于排序
retrieval_method|RetrievalMethod|召回方式
""")
scalar("Score","common","归一化排序分数，不是概率。",type="number",minimum=0,maximum=1)
enum("RetrievalMethod","keyword|vector|hybrid|explicit","context")
record("MemoryContent","context","用户记忆内容与可追溯来源。", """
text|NonEmptyText|记忆
kind|MemoryKind|偏好/事实/方法
source_refs|[](Ref)|原始依据
slot_key?|NonEmptyText|可发生冲突的逻辑槽
""")
enum("MemoryKind","preference|fact|procedure","context")
record("MemoryPolicy","context","读写独立开关，关闭后不能继续使用派生缓存。", """
revision|Revision|政策版本
read_enabled|Bool|允许读
contribute_enabled|Bool|允许贡献
scope|ScopeSelector|生效范围
retention_ms?|Duration|保留时间
""")
record("MemoryCandidate","context","推断候选不等于已保存事实。", """
id|ID|候选
content|MemoryContent|候选内容
origin|MemoryOrigin|明确要求或推断
target_scope|ScopeSelector|建议范围
""")
enum("MemoryOrigin","explicit|inferred","context")
record("MemorySelector","context","删除/召回筛选，不接受任意数据库条件。", """
ids?|[](ID)|指定记忆
scope?|ScopeSelector|限定范围
kind?|MemoryKind|类别
slot_key?|NonEmptyText|冲突槽
""",["删除空选择器必须拒绝；整范围删除须明确all_in_scope操作。"])
record("MemoryRecord","context","保存记忆及依赖。", """
id|ID|记忆
revision|Revision|版本
content|MemoryContent|内容
scope|Scope|有效范围
policy_ref|Ref|写入依据
created_at|Timestamp|保存时间
expires_at?|Timestamp|有效期
deleted_at?|Timestamp|逻辑删除时间
""")

# Tool registration/execution.
enum("EffectKind","read|internal_write|workspace_write|external_write|process|credential","tool")
record("Capability","tool","工具/模型能力摘要。", """
id|ID|能力名
description|NonEmptyText|能力说明
available|Bool|当前可用
schema_ref?|Ref|参数约束
""")
record("ToolSpec","tool","控制层注册的工具契约；描述检索不替代调用校验。", """
id|ID|稳定工具名
version|Version|固定schema版本
description|NonEmptyText|用途、限制和适用条件
input_schema|Schema|参数schema
output_schema|Schema|业务结果schema
categories|[](ID)|类别
required_capabilities|[](ID)|权限需求
effect|EffectKind|效果类别
provider_ref|Ref|有效提供方
equivalence_contract_ref?|Ref|严格等价替代约束
retry_policy_ref|Ref|恢复上限
feature_flag?|ID|产品开关
""")
record("ToolCandidate","tool","检索后交给LLM选择的摘要。", """
tool_ref|Ref|固定版本
description|NonEmptyText|描述
input_schema|Schema|本次可调用参数
effect|EffectKind|效果
score|Score|召回排序
""")
record("ToolCall","tool","模型只能提出工具名、参数和动作去重键。", """
tool_ref|Ref|固定工具版本
arguments|Object|依据input_schema再次校验
action_id|ID|跨重试保持不变的逻辑动作
""",["trusted_context、owner、approved等不是模型参数；参数被规范化后哈希再审批。"])
record("EffectRecord","tool","外部写账本记录意图、尝试和对账。", """
action_id|ID|逻辑动作
arguments_hash|Hash|规范参数摘要
provider_ref|Ref|真实提供方
business_key?|NonEmptyText|外部业务幂等键
attempt_ids|[](ID)|所有实际尝试
state|EffectState|效果是否已确认
receipt_ref?|Ref|外部回执
revision|Revision|账本版本
""")
record("ToolResult","tool","基础设施响应成功和业务成功分别表达。", """
call_ref|Ref|真实调用
status|ToolStatus|成功/失败/等待/未知效果
data?|Object|由该工具output_schema约束的业务数据
output_refs|[](Ref)|大结果/文件/证据
failure?|Failure|失败
effect_state|EffectState|副作用确定性
usage_ref|Ref|调用用量
next_cursor?|Cursor|分页
""",["failed须failure；unknown效果不得自动重放非幂等写；succeeded须实际回执或可验证只读结果。"])
enum("ToolStatus","succeeded|failed|waiting|cancelled|unknown","tool")
alias("ToolFailure","Failure")
record("RetryPolicy","tool","恢复次数和可重试类别有界。", """
max_attempts|Count|包括首次；1代表不重试
initial_backoff_ms|Duration|初始退避
max_backoff_ms|Duration|最大退避
retryable_categories|[](FailureCategory)|允许自动重试类别
allow_equivalent_provider|Bool|允许严格等价替代
""",["不得超过deadline/预算；未知写先reconcile；非等价替换交Agent决策。"])
record("ProviderBinding","tool","连接配置只引用秘密，不把秘密传入模型。", """
id|ID|提供方绑定
revision|Revision|配置版本
kind|ProviderKind|适配器种类
state|ConnectionState|当前状态
config_ref|Ref|非秘密配置
credential_ref?|Ref|密钥库句柄
account_connection_ref?|Ref|用户账号授权
""")
enum("ProviderKind","runtime|local|mcp|api|model","tool")
record("McpSession","tool","协议连接不能增加权限。", """
id|ID|连接会话
provider_ref|Ref|固定绑定
state|ConnectionState|连接状态
capability_revision|Revision|能力目录版本
expires_at?|Timestamp|截止时间
""")
record("AuditRecord","tool","审计只保留脱敏参数摘要和证据引用。", """
id|ID|记录
actor|Principal|真实主体
call_ref|Ref|调用
approval_ref?|Ref|授权依据
effect_state|EffectState|真实效果
usage_ref|Ref|尝试用量
created_at|Timestamp|时间
""")

# Workspace/Runner and delivery.
enum("IsolationMode","isolated_copy|worktree|native|cloud","workspace")
record("IncludeRules","workspace","基础快照收录策略，保护用户未提交改动。", """
include_uncommitted|Bool|包含获准未提交修改
include_untracked|Bool|包含未跟踪文件
include_paths|[](RelativePath)|显式包含
exclude_paths|[](RelativePath)|显式排除
max_total_bytes|Count|收录上限
""",["默认不收录密钥和缓存；超过上限失败或返回明确缺口，不静默截断。"])
record("ProjectBinding","workspace","通过本地可信选择器绑定的项目，云端仅存根句柄。", """
id|ID|项目绑定
revision|Revision|绑定版本
device_id|ID|设备
display_name|NonEmptyText|展示名
root_handle|ID|本地根句柄
capabilities|[](ID)|read/write/exec批准范围
state|ConnectionState|设备连接状态
""",["路径字符串不能自行产生绑定；Runner对realpath与链接再次校验。"])
record("BaseState","workspace","输入基础版本：提交、当前目录快照或成果。", """
id|ID|快照
kind|BaseKind|来源方式
source_ref|Ref|来源
manifest|Manifest|收录内容
include_rules|IncludeRules|明确收录策略
created_at|Timestamp|采集时间
""")
enum("BaseKind","commit|working_tree|artifact","workspace")
record("WorkspaceRecord","workspace","运行工作区位置与权限。", """
id|ID|工作区
revision|Version|文件树版本
project_binding_ref?|Ref|本地绑定
base_ref|Ref|基础快照
mode|IsolationMode|隔离方式
writer_agent_ref|Ref|当前写实例
root_handle|ID|Runner/沙箱句柄
environment_ref?|Ref|环境状态
state|WorkspaceState|可用状态
""")
enum("WorkspaceState","allocating|ready|busy|releasing|released|failed","workspace")
record("DependencyRequirement","workspace","声明环境需要，不把shell安装字符串当依赖契约。", """
kind|DependencyKind|系统/语言/包
name|NonEmptyText|例如python、go
version_constraint|NonEmptyText|版本要求
source_profile_ref?|Ref|管理员批准的来源
required|Bool|必需
""")
enum("DependencyKind","system|runtime|package","workspace")
record("EnvironmentTemplate","workspace","预装优先；按需安装须有权限、来源及验收。", """
id|ID|模板
version|Version|固定版本
dependencies|[](DependencyRequirement)|依赖
setup_actions|[](ProcessSpec)|受控初始化命令
verification_actions|[](ProcessSpec)|真实检查
network_policy_ref|Ref|网络策略
""")
record("EnvironmentRecord","workspace","真实环境结果，文字声称安装成功不能标记ready。", """
id|ID|环境
workspace_ref|Ref|工作区
template_ref?|Ref|初始化模板
status|EnvironmentState|准备状态
dependency_evidence_refs|[](Ref)|版本/安装证据
setup_process_refs|[](Ref)|实际进程
failure?|Failure|失败
revision|Revision|状态版本
""")
enum("EnvironmentState","unprepared|preparing|ready|failed|released","workspace")
record("EnvVar","workspace","显式环境变量；秘密值只由Runner/服务注入。", """
name|NonEmptyText|变量名
value|Text|非秘密值
""")
record("ProcessSpec","workspace","argv模式优先；shell模式是单独能力。", """
workspace_ref|Ref|工作区版本
executable|NonEmptyText|可执行文件或批准句柄
argv|[](Text)|独立参数数组
cwd|RelativePath|根内工作目录，.表示根
environment|[](EnvVar)|额外非秘密环境变量
timeout_ms|Duration|最大运行时间
shell_command?|NonEmptyText|shell模式命令
shell_profile_ref?|Ref|获准shell配置
""",["timeout必须>0；shell_command和shell_profile_ref同时出现；shell模式argv必须为空；Runner执行真实OS策略；超时终止进程树并报告残留。"])
record("ProcessRecord","workspace","启动返回进程句柄，实际结果使用poll。", """
id|ID|进程
spec|ProcessSpec|实际配置
status|ProcessState|进程状态
started_at|Timestamp|启动时间
ended_at?|Timestamp|结束时间
exit_code?|ExitCode|真实退出码；未结束缺省
stdout_ref?|Ref|输出内容
stderr_ref?|Ref|错误输出
output_cursor?|Cursor|未读日志
change_set_ref?|Ref|命令造成的改动
failure?|Failure|启动/终止失败
""")
enum("ProcessState","starting|running|exited|stopping|stopped|lost|failed","workspace")
scalar("ExitCode","workspace","真实进程退出码；不能用缺省0表示成功。",type="integer",minimum=-2147483648,maximum=4294967295)
record("FileEntry","workspace","文件元数据，路径均相对根。", """
path|RelativePath|路径
kind|FileKind|文件/目录/链接
size_bytes|Count|字节数
content_hash?|Hash|普通文件摘要
content_ref?|Ref|获准读取引用
""")
enum("FileKind","file|directory|symlink","workspace")
record("FileContent","workspace","有限文本；大文件以引用和游标读取。", """
workspace_ref|Ref|工作区版本
path|RelativePath|根内路径
encoding|NonEmptyText|例如utf-8
text|Text|本页内容
content_hash|Hash|整个文件摘要
location|Location|页/行范围
next_cursor?|Cursor|下一页
""")
TYPES["FileContent"]["properties"]["text"]={"type":"string","maxLength":65536,"description":"实际UTF-8片段；Runner同时限定返回64KiB，不扩大通用Text。"}
record("ChangeUnit","workspace","可审阅与选择的改动单位。", """
id|ID|改动块ID
path|RelativePath|文件
kind|ChangeKind|修改/新增/删除/改名
before_ref?|Ref|改前版本
after_ref?|Ref|改后版本
location?|Location|文本改动位置
patch_ref?|Ref|差异内容
binary|Bool|二进制不能行级合并
""")
enum("ChangeKind","add|modify|delete|rename","workspace")
record("ChangeSet","workspace","Diff绑定具体输入版本；不能覆盖用户之后的编辑。", """
id|ID|变更集
base_ref|Ref|基础文件树
target_ref|Ref|修改后文件树
units|[](ChangeUnit)|可选择改动
provenance_refs|[](Ref)|命令/模型动作来源
revision|Revision|登记版本
""",["局部接受/撤销先校验当前文件摘要；冲突返回新review，不盲写；撤销后测试旧报告失效。"])
record("MergeResult","workspace","合并可能有冲突，不能简单返回成功字符串。", """
status|MergeStatus|已合并或需冲突处理
workspace_ref|Ref|实际当前文件树
applied_unit_ids|[](ID)|确实应用的块
conflict_unit_ids|[](ID)|阻塞块
change_set_ref?|Ref|合并结果
revalidation_required|Bool|旧验证是否失效
""")
enum("MergeStatus","merged|partial|conflicted|unchanged","workspace")
record("ArtifactRecord","workspace","用户可编辑、预览、导出的版本化成果。", """
id|ID|成果
version|Version|内容版本
title|NonEmptyText|展示名
format_kind|NonEmptyText|例如markdown/csv/source_code
media_type|NonEmptyText|MIME
content_ref|Ref|实际内容
size_bytes|Count|字节数
content_hash|Hash|摘要
provenance_refs|[](Ref)|生成/数据来源
verification_refs|[](Ref)|该版本证据
created_at|Timestamp|登记时间
""",["publish工具仅登记成果，不意味着公网发布；下载URL授权且短时有效。"])
record("ReviewSet","workspace","用户审阅交付或修改集。", """
id|ID|审阅
revision|Revision|版本
target_refs|[](Ref)|固定成果/变更版本
unit_ids|[](ID)|可选择单位
decision?|DeliveryDecision|最新用户意见
feedback_refs|[](Ref)|位置反馈
""")
record("ReviewDecision","workspace","用户意见独立于自动核验。", """
decision|DeliveryDecision|接受/拒绝/修改/部分接受
selected_unit_ids|[](ID)|partial_accept必需指定非空
feedback|Text|用户理由或修订
position?|Location|具体位置
expected_target_refs|[](Ref)|基线内容
""")
record("VerificationCheck","agent","实际执行/资料核验的证据，不能伪造运行。", """
id|ID|检查
kind|VerificationKind|命令/结构/引用/语义
requirement_ids|[](ID)|覆盖要求
state|CheckState|passed/failed/not_run/blocked
target_refs|[](Ref)|核验版本
process_ref?|Ref|命令检查必需
evidence_refs|[](Ref)|真实证据
summary|Text|解释及限制
""")
enum("VerificationKind","command|structure|reference|semantic|manual","agent")
record("RequirementVerdict","agent","语义核验逐条覆盖要求。", """
requirement_id|ID|要求
state|CheckState|判定
evidence_refs|[](Ref)|实际证据
reason|NonEmptyText|判定依据
limitations|[](NonEmptyText)|缺口
""")
record("VerificationReport","agent","结构检查+真实执行+语义判定，不替代用户审阅。", """
id|ID|报告
contract_ref|Ref|交付要求
target_refs|[](Ref)|成果版本
checks|[](VerificationCheck)|具体检查
verdicts|[](RequirementVerdict)|逐要求结果
outcome|Outcome|总体结果
limitations|[](NonEmptyText)|缺口
reviewer_model_config_ref?|Ref|语义评审模型
created_at|Timestamp|生成时间
""")

# Model contracts.
record("CapabilityRequirements","model","本次调用需要的模型能力。", """
tool_calling|Bool|工具协议
structured_output|Bool|结构化结果
vision|Bool|图像输入
minimum_context_tokens|Count|最小上下文
minimum_output_tokens|Count|最小输出
""")
enum("Protocol","text|tool_calls|json_schema","model")
record("ModelCatalogEntry","model","管理员模型目录，不返回密钥。", """
id|ID|稳定目录ID
provider_ref|Ref|提供方
display_name|NonEmptyText|展示名
context_limit_tokens|Count|上下文窗口
output_limit_tokens|Count|输出上限
capabilities|[](ID)|协议能力
status|ProviderState|启停状态
revision|Revision|目录版本
""")
record("ResolvedModelPolicy","model","继承链与用户来源可核验。", """
id|ID|模型政策
revision|Revision|政策版本
mode|ModelMode|explicit或auto；inherit最终解析为父政策
fixed_model_id?|ID|固定模型
allowed_model_ids|[](ID)|Auto候选集
source_input_ref|Ref|明确用户选择
parent_policy_ref?|Ref|继承链
""")
record("ResolvedModelConfig","model","实际调用配置随用量记录。", """
model_id|ID|实际目录模型
catalog_revision|Revision|目录版本
provider_ref|Ref|绑定版本
policy_ref|Ref|模型政策
max_output_tokens|Count|输出预算
reasoning_level?|NonEmptyText|管理员登记支持值
temperature?|Temperature|提供方支持才可配置
""")
scalar("Temperature","model","提供方适配器可进一步缩小范围。",type="number",minimum=0,maximum=2)
record("Message","model","提供方无关消息，不包含私密思维链要求。", """
role|MessageRole|来源角色
content_refs|[](Ref)|有序内容块
tool_call_ref?|Ref|tool消息关联
""")
record("ModelOutput","model","文本与工具建议分别表达。", """
attempt_id|ID|实际尝试
actual_config|ResolvedModelConfig|真实配置
text|Text|可见模型结果
tool_calls|[](ToolCall)|拟执行工具；尚未授权
structured_data?|Object|受output_schema约束的结果
finish_reason|FinishReason|正常/工具/截断等
usage|Usage|已知用量
""")
enum("FinishReason","stop|tool_calls|length|refusal|error|cancelled","model")
alias("ModelFailure","Failure")

# Runs / approval / persistent event items.
record("Conversation","run","会话不等于Task；首期单用户仍有独立主体。", """
id|ID|会话
owner_id|ID|服务注入用户
title|NonEmptyText|标题
revision|Revision|会话版本
project_ref?|Ref|可选本地/云项目绑定
model_policy_ref|Ref|会话模型选择
memory_policy|MemoryPolicy|独立读写开关
created_at|Timestamp|创建时间
updated_at|Timestamp|修改时间
""")
record("InputRecord","run","原文追加保存，不覆盖已有输入。", """
id|ID|输入
conversation_id|ID|会话
turn_id|ID|轮次
text|Text|用户原文
attachment_refs|[](Ref)|获准附件
created_at|Timestamp|提交时间
""")
record("TaskRecord","run","跨会话关联任务需显式绑定和版本冲突处理。", """
id|ID|任务
revision|Revision|目标版本
conversation_refs|[](Ref)|关联会话
frame_ref?|Ref|正式理解
active_run_refs|[](Ref)|运行
artifact_refs|[](Ref)|成果
created_at|Timestamp|创建时间
""")
record("RunRecord","run","调度执行实体；任务历史有多个Run。", """
id|ID|Run
task_id|ID|任务
conversation_id|ID|入口会话
revision|Revision|状态版本
status|RunStatus|当前状态
root_agent_ref?|Ref|根实例
frame_ref?|Ref|当前任务理解
plan_ref?|Ref|可选图
budget|Budget|上限
outcome?|Outcome|终态
created_at|Timestamp|受理时间
ended_at?|Timestamp|实际结束
""")
record("ApprovalRequest","run","审批绑定动作、参数与资源版本。", """
id|ID|审批
revision|Revision|审批版本
action_id|ID|动作
arguments_hash|Hash|规范参数
resource_refs|[](Ref)|预期目标版本
effect|EffectKind|效果
summary|NonEmptyText|用户可读动作
mode|ApprovalMode|当前政策
status|ApprovalStatus|等待/批准等
expires_at|Timestamp|有效期
""")
enum("ApprovalStatus","pending|approved|declined|expired|cancelled|stale","run")
record("ApprovalDecision","run","由用户或批准的审查服务签发，LLM工具参数不含批准结果。", """
decision|ApprovalDecisionKind|单次/限定持续/拒绝/取消
expected_arguments_hash|Hash|对应动作参数
expected_resource_refs|[](Ref)|对应版本
scope_selector?|ScopeSelector|限定持续范围
expires_at?|Timestamp|持续授权截止
reason|Text|理由
""",["approve_scoped必需范围和有效期；不能批准原主体没有的权限；审批后必须recheck。"])
record("ApprovalGrant","run","授权结果不是无限期全局允许。", """
id|ID|授权
approval_ref|Ref|审批版本
actor|Principal|真实批准者
decision|ApprovalDecision|用户决定
issued_at|Timestamp|签发时间
""")
record("UserControl","run","补充、排队、替换、取消、先交现有成果语义明确。", """
mode|ControlMode|干预方式
input_ref?|Ref|新要求；steer/enqueue/replace必需
preserve_refs|[](Ref)|明确保留的成果
reason|Text|解释
""",["正在执行的调用在安全边界收到修订；不可撤销外部动作对账后如实展示。"])
record("Transition","run","内部状态转移提案。", """
from_state|RunStatus|预期原状态
to_state|RunStatus|目标状态
reason|NonEmptyText|转移依据
evidence_refs|[](Ref)|真实证据
""")
record("InteractionItem","run","稳定前端交互对象，不依赖猜模型文本。", """
id|ID|交互项
conversation_id|ID|会话
run_id?|ID|运行
type|ItemType|消息/工具/文件/审批等
status|ItemStatus|交互状态
revision|Revision|项版本
text|Text|可见内容
resource_refs|[](Ref)|关联真实资源
created_at|Timestamp|开始
updated_at|Timestamp|最近更新
""")
record("ItemPatch","run","增量文本不可与整段替换混淆。", """
item_id|ID|项
base_revision|Revision|原版本
status?|ItemStatus|新状态
text_delta?|Text|追加文本
replacement_text?|Text|完整替换
resource_refs?|[](Ref)|替换资源
""",["text_delta与replacement_text不能同时存在；至少一个变更字段；项终态不能继续delta。"])
record("EventEnvelope","run","持久事件有序号、版本与可追溯项。", """
event_id|ID|事件去重键
stream_id|ID|作用域流
seq|Revision|单调流序号
type|NonEmptyText|注册事件名
schema_version|Version|事件协议版本
occurred_at|Timestamp|提交时间
item_ref?|Ref|交互项
payload_ref|Ref|固定类型的事件payload
base_revision?|Revision|应用前版本
result_revision?|Revision|应用后版本
""")
record("Checkpoint","run","引用跨模块已提交版本，不能声称撤销外部动作。", """
id|ID|检查点
run_ref|Ref|运行版本
schema_version|Version|快照格式
committed_event_seq|Revision|最后提交事件
domains|[](DomainCheckpoint)|各域固定版本
pending_action_refs|[](Ref)|待对账动作
created_at|Timestamp|提交时间
""")
record("DomainCheckpoint","run","一个域的恢复指针。", """
domain|ID|域名
resource_ref|Ref|固定版本
lease_ref?|Ref|可选控制租约
""")
record("BudgetReservation","run","所有重试和子Agent共享父预算账本。", """
id|ID|预留
parent_ref?|Ref|父预留
estimates|ResourceVector|预留量
settled_usage_refs|[](Ref)|尝试账单
status|ReservationState|预留状态
revision|Revision|账本版本
""")
enum("ReservationState","reserved|partially_settled|settled|released","run")
record("TriggerSpec","run","触发Run与调度图节点分开，首版旗标可关闭。", """
id|ID|触发器
revision|Revision|版本
task_ref|Ref|目标任务
schedule|NonEmptyText|规范时间规则
timezone|NonEmptyText|IANA时区
overlap_policy|OverlapPolicy|重叠处理
enabled|Bool|开关
""")
enum("OverlapPolicy","queue|skip|parallel","run")

# Administrative/shared structures, no arbitrary config patch endpoints.
record("ConfigurationVersion","support","管理员配置发布经过校验后成为有效版本。", """
id|ID|配置域
revision|Revision|版本
model_refs|[](Ref)|模型目录
provider_refs|[](Ref)|工具/搜索绑定
environment_template_refs|[](Ref)|环境模板
feature_flags|[](FeatureFlag)|能力开关
approval_policy_ref|Ref|审批政策
storage_policy_ref|Ref|存储部署政策
state|ProviderState|发布状态
""")
record("FeatureFlag","support","关闭能力在发现、调用、恢复和子Agent处均执行。", """
id|ID|能力旗标
enabled|Bool|当前允许
scope|ScopeSelector|适用产品范围
reason|Text|说明
""")
record("StoragePolicy","support","云端权威或本地权威部署选项仍待用户确认。", """
mode|StorageMode|云权威/本地权威
local_cache_enabled|Bool|缓存仅加速，不产生第二权威
retention_ms?|Duration|历史保留
encrypted|Bool|落盘加密要求
revision|Revision|政策版本
""")
enum("StorageMode","cloud_authoritative|local_authoritative","support")
record("AccountConnection","support","私人账号授权区别于管理员平台API配置。", """
id|ID|用户连接
provider_ref|Ref|服务
state|ConnectionState|状态
granted_scopes|[](ID)|用户批准范围
credential_ref?|Ref|服务端秘密句柄；普通HTTP视图剔除
expires_at?|Timestamp|截止
revision|Revision|连接版本
""")
record("ExtensionManifest","support","能力包安装、依赖、校验与启停。", """
id|ID|插件
version|Version|版本
content_hash|Hash|摘要
skill_refs|[](Ref)|技能
tool_refs|[](Ref)|工具
dependency_refs|[](Ref)|依赖
requested_capabilities|[](ID)|请求权限
state|ProviderState|启用状态
""")
record("CacheKey","support","稳定前缀与结果缓存是两种缓存，不可混为一谈。", """
namespace|ID|隔离命名空间
scope|Scope|主体范围
dependency_refs|[](Ref)|所有会影响结果的版本
parameters_hash|Hash|规范参数
policy_ref|Ref|策略版本
freshness|FreshnessPolicy|时效要求
""")
record("CacheRecord","support","缓存命中仍校验权限、版本和时效。", """
key|CacheKey|键
value_ref|Ref|结果
created_at|Timestamp|产生时间
expires_at|Timestamp|失效时间
content_hash|Hash|结果摘要
""")
record("TraceSpan","support","脱敏链路观测；不保存密钥/私密思维链。", """
trace_id|ID|链路
span_id|ID|片段
parent_span_id?|ID|父片段
operation_id|ID|操作
attempt_id?|ID|执行尝试
domain_refs|[](Ref)|版本
started_at|Timestamp|开始
ended_at?|Timestamp|结束
usage_ref?|Ref|消耗
failure?|Failure|错误
""")
record("EvaluationResult","support","成本统计包含失败、重试和用户返工。", """
id|ID|评测
candidate_manifest_ref|Ref|候选
baseline_manifest_ref|Ref|基线
dataset_ref|Ref|固定样本
accepted_count|Count|可接受成果数量
attempt_count|Count|所有尝试
total_usage_ref|Ref|总消耗
report_ref|Ref|质量/耗时报告
""")
record("CapabilityPolicy","run","有效权限交集上限，配置不等于新用户授权。","id|ID|政策\nrevision|Revision|修订\nallowed_capabilities|[](ID)|允许能力\ndenied_capabilities|[](ID)|显式禁止\nresource_scope|ScopeSelector|资源范围\nnetwork_allowlist|[](NonEmptyText)|批准网络域\nfeature_flag_refs|[](Ref)|能力开关\nparent_policy_ref?|Ref|父政策",["deny优先；子策略只能收窄；Runner执行能力还须本机实际批准。"])
record("ApprovalRule","run","可匹配动作的审批规则。","id|ID|规则\neffects|[](EffectKind)|效果类别\ncapabilities|[](ID)|能力\nscope|ScopeSelector|适用范围\nrequire_user|Bool|必须用户决定\nallow_assisted_review|Bool|是否可辅助审查\nmax_grant_duration_ms|Duration|授权有效期上限")
record("ApprovalPolicy","run","三模式在现有权限内应用规则。","id|ID|政策\nrevision|Revision|修订\ndefault_mode|ApprovalMode|默认模式\nallowed_modes|[](ApprovalMode)|可选模式\nrules|[](ApprovalRule)|审批要求\nreviewer_profile_ref?|Ref|辅助审查配置",["模式不能覆盖require_user的高影响规则；审批结果必须签名来源，模型建议不能自批。"])
record("CachePolicy","support","结果/前缀/在途缓存的不同策略。","id|ID|政策\nrevision|Revision|修订\nlayer|CacheLayer|缓存层\nttl_ms|Duration|生命周期\nmax_age_ms|Duration|可接受陈旧程度\nmax_entry_bytes|Count|单条最大值\nnegative_ttl_ms|Duration|明确不存在/短期失败缓存\nallowed_effects|[](EffectKind)|可缓存效果\nshared_across_principals|Bool|是否明确公共资源",["敏感/私有内容不跨主体；结果缓存不接受写/审批/当前进程状态；前缀命中以provider usage为准。"])
enum("CacheLayer","model_prefix|source_parse|retrieval|context_derived|read_result|single_flight","support")
record("EquivalenceContract","tool","提供方自动切换前的严格等价登记。","id|ID|契约\nversion|Version|版本\ntool_ref|Ref|同一能力契约\nprovider_refs|[](Ref)|经过核验的提供方\ninput_schema_ref|Ref|相同参数语义\noutput_schema_ref|Ref|相同结果语义\ninformation_scope_ref|Ref|相同信息范围\neffect|EffectKind|相同效果\nidempotency_namespace|ID|同逻辑动作命名空间\nverification_refs|[](Ref)|等价测试证据\nstate|ProviderState|是否已批准",["网页摘要与原文读取不能默认等价；写提供方切换还须业务幂等可确认。"])
record("ReleaseManifest","support","可评测、恢复核对的不可变系统版本清单。","id|ID|发布\nversion|Version|版本\nruntime_version|Version|代码\ncontract_version|Version|协议\nprompt_refs|[](Ref)|提示词版本\nskill_refs|[](Ref)|技能版本\ntool_refs|[](Ref)|工具schema\nadapter_refs|[](Ref)|适配器\nmodel_catalog_ref|Ref|模型目录\nconfiguration_ref|Ref|配置\nenvironment_template_refs|[](Ref)|环境\nevaluation_report_ref|Ref|回归证据\ncontent_hash|Hash|清单摘要")
record("ExecutionLease","run","Run/节点恢复租约归Run，与Agent对话控制租约区分。","id|ID|租约\nrun_id|ID|Run\nnode_id?|ID|可选节点\nholder|Principal|当前执行服务/worker\nfencing_token|Revision|单调栅栏\nexpires_at|Timestamp|过期\nrevision|Revision|租约修订")
record("McpTransportConfig","tool","协议适配配置，不包含秘密或任意任务代码。","id|ID|配置\nversion|Version|固定版本\ntransport|McpTransport|HTTP或stdio\nendpoint?|URL|HTTP地址\nlauncher_template_ref?|Ref|管理员批准的stdio启动模板\ncredential_ref?|Ref|秘密库句柄\nprotocol_version|Version|协议配置\ntimeout_ms|Duration|超时",["HTTP需endpoint；stdio需launcher_template_ref且不执行模型构造的任意命令；敏感headers由适配器注入。"])
enum("McpTransport","http|stdio","tool")
TYPES["McpTransportConfig"]["oneOf"]=[{"properties":{"transport":{"const":"http"}},"required":["endpoint"],"not":{"required":["launcher_template_ref"]}},{"properties":{"transport":{"const":"stdio"}},"required":["launcher_template_ref"],"not":{"required":["endpoint"]}}]
record("ModelPricing","model","账单估算使用管理员核验的固定价格版本。","id|ID|价格\nversion|Version|版本\ncurrency|Currency|币种\ninput_per_million_tokens|Decimal|输入单价\noutput_per_million_tokens|Decimal|输出单价\ncached_input_per_million_tokens?|Decimal|提供方缓存价格\neffective_at|Timestamp|生效\nsource_ref|Ref|管理员依据")
scalar("Currency","common","ISO币种标签，金额不可混币种直接相加。",type="string",pattern="^[A-Z]{3}$")
record("PolicyDraft","support","管理员登记一个有明确类型的政策。","name|ID|稳定名\npayload|PolicyPayload|有类型草案")
TYPES["PolicyPayload"]={"description":"政策按类型分别验证，不使用任意configuration_patch。","oneOf":[ref(x) for x in ["CapabilityPolicy","ApprovalPolicy","CachePolicy","StoragePolicy","RetryPolicy"]]}
OWNERS["PolicyPayload"]="support";RULES["PolicyPayload"]=["平台登记后重新分配修订；有效权限仍受用户/本机批准约束。"]

# Semantic rules whose truth depends on runtime state remain explicit code gates.
TYPES["TaskGraph"]["properties"]["planning"]={"type":"string","enum":["steps","dag"],"description":"图仅用于步骤清单或DAG。"}
TYPES["ScopeSelector"]["minProperties"]=1
TYPES["ProcessSpec"]["properties"]["timeout_ms"]["minimum"]=1
TYPES["ProcessSpec"]["dependentRequired"]={"shell_command":["shell_profile_ref"],"shell_profile_ref":["shell_command"]}
TYPES["ProcessSpec"]["allOf"]=[{"if":{"required":["shell_command"]},"then":{"properties":{"argv":{"maxItems":0}}}}]
TYPES["ItemPatch"]["not"]={"required":["text_delta","replacement_text"]}
TYPES["ItemPatch"]["anyOf"]=[{"required":[x]} for x in ["status","text_delta","replacement_text","resource_refs"]]
TYPES["ApprovalDecision"]["allOf"]=[{"if":{"properties":{"decision":{"const":"approve_scoped"}},"required":["decision"]},"then":{"required":["scope_selector","expires_at"]}}]
TYPES["ReviewDecision"]["allOf"]=[{"if":{"properties":{"decision":{"const":"partial_accept"}},"required":["decision"]},"then":{"properties":{"selected_unit_ids":{"minItems":1}}}}]

# Explicit operation catalog: all external contracts exclude trusted context.
def operation(id, channel, owner, nodes, request, response, effect="read", rules=(),
              method=None, path=None, auth="user", errors=(), feature=None):
    if (channel,id) in {(o["channel"],o["id"]) for o in OPERATIONS}: raise ValueError("duplicate operation "+channel+":"+id)
    OPERATIONS.append(dict(id=id,channel=channel,owner=owner,nodes=nodes.split(),request=request,response=response,
      effect=effect,rules=list(rules),method=method,path=path,auth=auth,errors=list(errors),feature=feature,
      implemented=False))

def endpoint(id, method, path, owner, nodes, description, spec, response, effect="read", rules=(), auth="user",feature=None):
    name="".join(x.capitalize() for x in id.split("."))+"Request"
    record(name,owner,description,spec,rules)
    operation(id,"http",owner,nodes,name,response,effect,rules,method,path,auth,feature=feature)

def tool(id,owner,nodes,description,spec,response,effect="read",rules=(),feature=None):
    name="Tool"+"".join(x.capitalize() for x in id.split("."))+"Input"
    record(name,owner,description,spec,rules)
    operation(id,"tool",owner,nodes,name,response,effect,rules,auth="agent",feature=feature)

def facade(id,owner,nodes,request,response,effect="read",rules=()):
    operation(id,"runtime",owner,nodes,request,response,effect,rules,auth="service")

# Reusable requests/output collections, each with a fully typed element.
record("EmptyRequest","common","无业务参数，仍需要可信上下文。","")
record("IdRequest","common","读取一个获准资源。","id|ID|资源ID")
record("RefRequest","common","读取一个固定版本的获准资源。","ref|Ref|资源版本")
record("TextContent","common","短内容返回。","text|Text|内容\nsource_refs|[](Ref)|来源\nnext_cursor?|Cursor|下一页")
record("BlobReceipt","common","完成上传后才可引用，分片文件不作为有效输入。","asset_ref|Ref|已发布素材\nsize_bytes|Count|实际大小\ncontent_hash|Hash|摘要\nmedia_type|NonEmptyText|检测格式")
record("DownloadTicket","common","授权下载句柄，不能视为公开URL。","url|URL|短期地址\nexpires_at|Timestamp|有效期\nresource_ref|Ref|目标\ncontent_hash|Hash|摘要")
record("DraftPreview","intent","发送前只读理解提示；发送后不得冒充已执行。","draft_revision|Revision|对应草稿\ninterpretation|Interpretation|提示\nmodel_config_ref|Ref|实际模型\nexpires_at|Timestamp|提示有效期")
record("ResolvedReference","context","可访问内容入口。","record|ReferenceRecord|来源\ncitations|[](Citation)|主张定位\nnext_cursor?|Cursor|下一页")
record("ReadResult","context","实际读取片段。","reference_ref|Ref|来源版本\ntext|Text|片段\nlocation|Location|位置\nnext_cursor?|Cursor|下一页")
record("DiscoveryResult","tool","先过滤权限、再检索，最终由LLM选择调用。","tools|[](ToolCandidate)|工具候选\nagents|[](AgentCandidate)|子Agent候选\nregistry_revision|Revision|目录版本")
record("AgentWaitResult","agent","等待不是轮询造成功；超时返回仍在运行。","instances|[](AgentInstance)|最新状态\nresults|[](AgentResult)|已完成结果\nnext_cursor?|Cursor|增量游标\ntimed_out|Bool|本次等待到期")
record("SchedulerResult","agent","代码调度结果，禁止LLM直接跳过依赖。","ready_node_ids|[](ID)|可执行\nblocked_node_ids|[](ID)|受阻\nreserved_refs|[](Ref)|实际预留")
record("CancellationResult","run","取消异步传播；停止与效果对账分别记录。","target_refs|[](Ref)|目标\nstopped_refs|[](Ref)|已停止\npending_refs|[](Ref)|仍处理中\nunknown_effect_refs|[](Ref)|未确认效果\npreserved_refs|[](Ref)|保留成果")
record("DefinitionDiff","agent","角色历史比较。","definition_id|ID|角色\nbase_ref|Ref|基线\ntarget_ref|Ref|目标\nchanged_fields|[](NonEmptyText)|改变字段\nchange_set_ref|Ref|可审阅内容")
record("ValidationReport","common","结构/政策校验结果，不自动执行被校验对象。","valid|Bool|是否通过\nnormalized_ref?|Ref|规范化对象\nviolations|[](ValidationIssue)|问题\nevidence_refs|[](Ref)|依据")
record("ValidationIssue","common","具体字段/规则错误。","code|ID|错误码\nfield_pointer?|NonEmptyText|JSON Pointer\nmessage|NonEmptyText|原因\nrule|NonEmptyText|规则名")
record("RunnerPairing","workspace","配对凭据仅用户与Runner交互，禁止进入模型。","pairing_id|ID|配对事务\nverification_code|NonEmptyText|短期一次码\nexpires_at|Timestamp|截止\napproval_url|URL|用户确认入口")
record("RunnerDevice","workspace","Runner在线状态与本机可执行能力。","device_id|ID|设备\nrevision|Revision|注册版本\ndisplay_name|NonEmptyText|名称\nstate|ConnectionState|状态\ncapabilities|[](ID)|执行能力\nlast_seen_at|Timestamp|最近心跳")
record("RunnerCommand","workspace","服务签发的命令信封，不接受模型直连。","command_id|ID|逻辑命令\noperation_id|ID|接口操作\nrequest_ref|Ref|固定业务参数\ntrusted_context|TrustedExecutionContext|服务签发身份范围\nfencing_token|Revision|过期执行防护\nexpires_at|Timestamp|命令期限\nsignature|NonEmptyText|会话密钥签名")
record("CacheLookupResult","support","miss不当错误；命中仍校验依赖。","hit|Bool|是否命中\nrecord?|CacheRecord|命中条目\nmiss_reason?|NonEmptyText|失效/不存在原因")
record("CompatibilityReport","run","恢复前兼容性与版本缺口。","compatible|Bool|能否恢复\nmissing_refs|[](Ref)|不可用资源\nstale_refs|[](Ref)|版本不符\nmigration_ref?|Ref|批准迁移\nblocking_reasons|[](NonEmptyText)|阻碍")
record("RecoveryDecision","common","恢复建议不是任意换模型/工具的许可。","action|RecoveryAction|可执行恢复\nretry_after_ms?|Duration|等待\nreplacement_ref?|Ref|仅已授权等价提供方/Auto模型\nreason|NonEmptyText|依据")
enum("RecoveryAction","retry|reconcile|switch_equivalent|ask_agent|ask_user|stop","common")
record("DeletionReceipt","common","删除回执含派生失效，不掩盖异步物理清除。","deletion_id|ID|删除事务\ndeleted_refs|[](Ref)|逻辑删除\ninvalidated_refs|[](Ref)|索引/缓存失效\nphysical_cleanup_pending|Bool|物理回收状态")

def page(name,element,owner):
    record(name,owner,"稳定筛选条件的分页结果。",f"items|[]({element})|本页\nnext_cursor?|Cursor|续页\nsnapshot_revision|Revision|读取版本")
for n,t,o in [
 ("ConversationPage","Conversation","run"),("ItemPage","InteractionItem","run"),("DefinitionPage","AgentDefinitionVersion","agent"),
 ("CandidatePage","AgentCandidate","agent"),("BoardPage","BoardEntry","agent"),("SkillPage","SkillSpec","agent"),
 ("MemoryPage","MemoryRecord","context"),("RetrievalPage","RetrievalHit","context"),("ArtifactPage","ArtifactRecord","workspace"),
 ("ModelPage","ModelCatalogEntry","model"),("ToolPage","ToolSpec","tool"),("EventPage","EventEnvelope","run"),
 ("TracePage","TraceSpan","support"),("FilePage","FileEntry","workspace"),("ReferencePage","ReferenceRecord","context"),
 ("DevicePage","RunnerDevice","workspace"),("ConnectionPage","AccountConnection","support"),("CheckPage","VerificationCheck","agent"),
 ("ExtensionPage","ExtensionManifest","support")]: page(n,t,o)

# HTTP: accounts are authenticated upstream; resource ownership is never body-controlled.
endpoint("conversations.create","POST","/v1/conversations","run","ui ingress run.history model.policy","创建会话。",
 "title|NonEmptyText|标题\nmodel_choice|ConversationModelChoice|用户选定模型\nproject_ref?|Ref|获准项目\nmemory_policy|MemoryPolicy|记忆控制","Conversation","internal_write",["principal由认证注入；模型目录不可用时返回model_unavailable，不静默选择。"])
record("ConversationModelChoice","model","用户选择当前会话模型；无法选inherit。","mode|ConversationModelMode|explicit或auto\nmodel_id?|ID|固定模型ID\nallowed_model_ids?|[](ID)|Auto授权范围")
enum("ConversationModelMode","explicit|auto","model")
TYPES["ConversationModelChoice"]["allOf"]=[{"if":{"properties":{"mode":{"const":"explicit"}},"required":["mode"]},"then":{"required":["model_id"],"not":{"required":["allowed_model_ids"]}}},{"if":{"properties":{"mode":{"const":"auto"}},"required":["mode"]},"then":{"required":["allowed_model_ids"],"properties":{"allowed_model_ids":{"minItems":1}},"not":{"required":["model_id"]}}}]
endpoint("conversations.list","GET","/v1/conversations","run","ui run.history","查询自己的会话。","cursor?|Cursor|续页\nlimit?|PageLimit|页大小","ConversationPage")
scalar("PageLimit","common","每页数量。",type="integer",minimum=1,maximum=100,default=20)
endpoint("conversations.get","GET","/v1/conversations/{conversation_id}","run","ui run.history","读取会话。","conversation_id|ID|路径会话","Conversation")
endpoint("conversations.configure","PATCH","/v1/conversations/{conversation_id}","run","ui run.history model.policy context.memory.policy","修改会话设置。","conversation_id|ID|路径会话\npatch|ConversationPatch|白名单修改","Conversation","internal_write",["需expected_revision；模型变化默认只影响下一安全调用边界，不改写已产生的结果。"])
record("ConversationPatch","run","至少一个字段，删除项目用显式detach。","title?|NonEmptyText|新标题\nmodel_choice?|ConversationModelChoice|新模型\nmemory_policy?|MemoryPolicy|记忆设置\nproject_ref?|Ref|新项目\ndetach_project?|Bool|解除绑定")
TYPES["ConversationPatch"]["minProperties"]=1
TYPES["ConversationPatch"]["not"]={"required":["project_ref","detach_project"]}
endpoint("conversations.items","GET","/v1/conversations/{conversation_id}/items","run","ui run.history run.events","可见交互记录。","conversation_id|ID|会话\ncursor?|Cursor|续页\nlimit?|PageLimit|页大小","ItemPage")
endpoint("intent.preview","POST","/v1/conversations/{conversation_id}/preview","intent","ui ingress intent.preview","草稿理解提示。","conversation_id|ID|会话\ndraft_revision|Revision|草稿版本\ntext|Text|原文\nattachment_refs|[](Ref)|材料","DraftPreview","read",["只读、短deadline；取消旧草稿；预览失败不阻止提交；不得创建Run或执行写。"])
endpoint("turns.submit","POST","/v1/conversations/{conversation_id}/turns","run","ui ingress run.history run.state intent.original intent.semantic intent.frame agent.loop","提交原文并受理Run。","conversation_id|ID|会话\ntext|Text|用户原文\nattachment_refs|[](Ref)|附件\ntask_id?|ID|继续已有任务\nexpected_task_revision?|Revision|继续任务必需\nbudget?|Budget|用户预算上限","RunRecord","internal_write",["同request_id+相同规范请求重放返回原Run；同键不同原文冲突；输入正文或附件至少一个非空。"])
endpoint("tasks.get","GET","/v1/tasks/{task_id}","run","ui run.history","读取任务。","task_id|ID|任务","TaskRecord")
endpoint("tasks.frame","GET","/v1/tasks/{task_id}/frame","intent","ui intent.frame","读取当前任务理解。","task_id|ID|任务","TaskFrame")
endpoint("tasks.plan","GET","/v1/tasks/{task_id}/plan","agent","ui agent.planning","读取可选任务图。","task_id|ID|任务","TaskGraph",rules=["无图返回missing，不能伪造空图。"])
endpoint("tasks.board","GET","/v1/tasks/{task_id}/board","agent","ui agent.board","读取共享结果板。","task_id|ID|任务\ncursor?|Cursor|续页\nlimit?|PageLimit|页大小","BoardPage")
endpoint("runs.get","GET","/v1/runs/{run_id}","run","ui run.state","运行状态。","run_id|ID|运行","RunRecord")
endpoint("runs.control","POST","/v1/runs/{run_id}/control","run","ui run.approval run.cancel intent.frame agent.planning","用户干预。","run_id|ID|运行\ncontrol|UserControl|控制指令","Acknowledgement","internal_write",["expected_revision必需；steer追加要求、enqueue下一轮、replace取消过期工作并开始新修订；202仅表示受理。"])
endpoint("runs.checkpoint","POST","/v1/runs/{run_id}/checkpoints","run","run.checkpoint","创建可恢复检查点。","run_id|ID|运行","Checkpoint","internal_write",["只采集已提交域版本；未决外部写保留到pending_action_refs；需expected_revision。"])
endpoint("runs.resume","POST","/v1/runs/{run_id}/resume","run","ui run.resume run.resume.lease run.resume.versions run.resume.access run.resume.effects run.resume.workspace run.resume.continue","从检查点恢复。","run_id|ID|运行\ncheckpoint_ref|Ref|目标检查点\nmode|RecoveryMode|resume或rerun","RunRecord","internal_write",["执行恢复先取得租约、复核权限与资源、对账未知写；rerun创建新Run，不能冒充结果复现。"])
enum("RecoveryMode","resume|rerun","run")
endpoint("events.read","GET","/v1/conversations/{conversation_id}/events","run","ingress run.events","分页读取历史事件。","conversation_id|ID|会话\ncursor?|Cursor|续页\nlimit?|PageLimit|页大小","EventPage")
endpoint("events.stream","GET","/v1/conversations/{conversation_id}/events/stream","run","ui ingress run.events","SSE续接。","conversation_id|ID|会话\ncursor?|Cursor|续接位置","EventEnvelope",rules=["Last-Event-ID与cursor同时存在必须一致；断点过旧返回410并提供快照入口；心跳不持久化。"])
endpoint("approvals.get","GET","/v1/approvals/{approval_id}","run","ui run.approval","审批详情。","approval_id|ID|审批","ApprovalRequest")
endpoint("approvals.decide","POST","/v1/approvals/{approval_id}/decisions","run","ui run.approval tool.invocation.approval tool.invocation.recheck","用户审批。","approval_id|ID|审批\ndecision|ApprovalDecision|批准范围","ApprovalGrant","internal_write",["expected_revision必需；参数/资源版本不一致返回stale；不能从LLM参数approved读取授权。"])
endpoint("assets.upload.begin","POST","/v1/assets/uploads","context","ui context.sources context.ingestion","申请上传事务。","file_name|NonEmptyText|展示文件名\nmedia_type|NonEmptyText|声称格式\nsize_bytes|UploadSize|总大小\ncontent_hash|Hash|整体摘要","UploadSession","internal_write")
scalar("UploadSize","context","单个上传最大100MiB，部署可降低。",type="integer",minimum=1,maximum=104857600)
record("UploadSession","context","二进制上传不塞入模型或普通JSON。","id|ID|上传ID\nput_url|URL|一次性上传地址\nexpires_at|Timestamp|截止\nmax_bytes|UploadSize|限制")
endpoint("assets.upload.complete","POST","/v1/assets/uploads/{upload_id}/complete","context","context.ingestion","确认上传并校验。","upload_id|ID|事务\ncontent_hash|Hash|整体摘要","BlobReceipt","internal_write",["只有真实字节/摘要/格式检查通过才发布asset_ref。"])
endpoint("references.resolve","POST","/v1/references/resolve","context","context.references","解析引用。","reference|Ref|目标","ResolvedReference")
endpoint("references.read","POST","/v1/references/read","context","context.references context.sources","读取位置。","reference|Ref|固定版本\nlocation?|Location|位置\ncursor?|Cursor|分页","ReadResult")
endpoint("sources.ingest","POST","/v1/tasks/{task_id}/sources","context","context.ingestion","摄取任务资料。","task_id|ID|任务\nsource_ref|Ref|材料\nparser_profile|ID|批准解析配置\nchunk_profile|ID|切分配置\nembedding_profile|ID|向量配置","IngestionRecord","internal_write",["异步状态preparing/running；索引发布CAS后才成为active。"])
endpoint("sources.delete","DELETE","/v1/tasks/{task_id}/sources/{source_id}","context","context.ingestion support.cache","删除资料及派生索引。","task_id|ID|任务\nsource_id|ID|材料","DeletionReceipt","internal_write",["expected_revision必需；权限内逻辑删除先阻断读取，异步物理清理可继续。"])
endpoint("sources.get","GET","/v1/tasks/{task_id}/sources/{source_id}","context","context.ingestion","读取当前资料摄取、解析与发布状态。","task_id|ID|任务\nsource_id|ID|材料ID","IngestionRecord",rules=["未发布时chunk_refs不供检索；pending状态只说明作业已受理。"])
endpoint("memory.list","GET","/v1/conversations/{conversation_id}/memories","context","context.memory context.memory.store","查看可见记忆。","conversation_id|ID|会话\ncursor?|Cursor|续页\nlimit?|PageLimit|页大小","MemoryPage")
endpoint("memory.forget","POST","/v1/conversations/{conversation_id}/memories/forget","context","context.memory.forget support.cache","删除用户选中的记忆。","conversation_id|ID|会话\nselector|MemorySelector|非空限定选择","DeletionReceipt","internal_write",["禁止空选择器全量删除；失效索引、摘要和缓存；后续调用不能读旧记忆派生块。"])
endpoint("definitions.create","POST","/v1/conversations/{conversation_id}/agents","agent","ui agent.definitions agent.definitions.validator agent.definitions.model_intent agent.definitions.repository","保存角色。","conversation_id|ID|会话\ndefinitions|DefinitionDrafts|批量草案\nbatch_policy|BatchPolicy|atomic或independent\nsource_input_ref|Ref|用户明确创建依据","DefinitionBatchResult","internal_write",["不会启动实例；显式模型缺失返回needs_resolution；会话名唯一；幂等client_definition_key。"])
scalar("DefinitionDrafts","agent","每次最多16个。",type="array",items=ref("AgentDefinitionDraft"),minItems=1,maxItems=16)
enum("BatchPolicy","atomic|independent","agent")
endpoint("definitions.list","GET","/v1/conversations/{conversation_id}/agents","agent","ui agent.definitions.discovery","列出绑定角色。","conversation_id|ID|会话\ncursor?|Cursor|续页\nlimit?|PageLimit|页大小","DefinitionPage")
endpoint("definitions.get","GET","/v1/conversations/{conversation_id}/agents/{definition_id}","agent","agent.definitions.repository","读取指定角色。","conversation_id|ID|会话\ndefinition_id|ID|角色","AgentDefinitionVersion")
endpoint("definitions.update","PATCH","/v1/conversations/{conversation_id}/agents/{definition_id}","agent","agent.definitions.change_service agent.definitions.validator agent.definitions.repository","修改角色。","conversation_id|ID|会话\ndefinition_id|ID|角色\npatch|DefinitionPatch|白名单字段\nsource_input_ref|Ref|用户修改来源","AgentDefinitionVersion","internal_write",["expected_revision必需；运行实例固定旧定义，不追随变更。"])
endpoint("definitions.diff","POST","/v1/conversations/{conversation_id}/agents/{definition_id}/diff","agent","agent.definitions.change_service","比较角色版本。","conversation_id|ID|会话\ndefinition_id|ID|角色\nbase_ref|Ref|基线\ntarget_ref|Ref|目标","DefinitionDiff")
endpoint("definitions.revert","POST","/v1/conversations/{conversation_id}/agents/{definition_id}/revert","agent","agent.definitions.change_service","恢复旧定义为新版本。","conversation_id|ID|会话\ndefinition_id|ID|角色\ntarget_ref|Ref|旧版本\nsource_input_ref|Ref|用户来源","AgentDefinitionVersion","internal_write",["CAS；创建新revision，保留历史；权限和模型配置重新校验。"])
endpoint("agents.get","GET","/v1/agents/{agent_id}","agent","ui agent.factory agent.loop","查看实例。","agent_id|ID|实例","AgentInstance")
endpoint("agents.cancel","POST","/v1/agents/{agent_id}/cancel","agent","ui agent.collaboration.cancel run.cancel","取消子树。","agent_id|ID|实例\nreason|NonEmptyText|理由","CancellationResult","internal_write")
endpoint("skills.list","GET","/v1/skills","agent","agent.skills support.extensions","可用技能摘要。","cursor?|Cursor|续页\nlimit?|PageLimit|页大小","SkillPage")
endpoint("projects.list","GET","/v1/devices","workspace","ui workspace.binding","查看已配对设备。","cursor?|Cursor|续页\nlimit?|PageLimit|页大小","DevicePage")
endpoint("projects.bind","POST","/v1/projects/bind","workspace","ui workspace.binding","绑定可信选择器结果。","device_id|ID|设备\nselection_token|NonEmptyText|Runner签发一次根选择凭据\ndisplay_name|NonEmptyText|名称\nrequested_capabilities|[](ID)|read/write/exec","ProjectBinding","internal_write",["根不由网页任意path字符串指定；一次凭据绑定当前用户和设备；批准后能力只能缩窄。"],feature="local_runner")
endpoint("projects.get","GET","/v1/projects/{project_id}","workspace","workspace.binding","项目绑定。","project_id|ID|项目","ProjectBinding",feature="local_runner")
endpoint("projects.unbind","DELETE","/v1/projects/{project_id}","workspace","workspace.binding run.cancel","撤销项目权限。","project_id|ID|项目","CancellationResult","internal_write",["立即失效新命令、控制租约和缓存；正在执行进程请求停止并对账。"],feature="local_runner")
endpoint("workspaces.get","GET","/v1/workspaces/{workspace_id}","workspace","workspace.isolation","工作区详情。","workspace_id|ID|工作区","WorkspaceRecord")
endpoint("workspaces.files","GET","/v1/workspaces/{workspace_id}/files","workspace","workspace.process","列文件。","workspace_id|ID|工作区\npath|RelativePath|相对目录\ncursor?|Cursor|续页\nlimit?|PageLimit|页大小","FilePage",feature="file_access")
endpoint("workspaces.changes","GET","/v1/workspaces/{workspace_id}/changes","workspace","ui workspace.changes","查看实际变更。","workspace_id|ID|工作区","ChangeSet")
endpoint("workspaces.merge","POST","/v1/workspaces/{workspace_id}/merge","workspace","workspace.changes","局部或全部合并。","workspace_id|ID|目标工作区\nchange_set_ref|Ref|候选变更集\nselected_unit_ids|[](ID)|明确选择\nexpected_workspace_version|Version|文件树基线","MergeResult","workspace_write",["选空列表拒绝；当前文件基线变化返回conflict；二进制按文件；重新核验成果。"],feature="file_write")
endpoint("workspaces.revert","POST","/v1/workspaces/{workspace_id}/revert","workspace","ui workspace.changes","撤销指定已应用变更。","workspace_id|ID|工作区\nchange_set_ref|Ref|可逆变更集\nselected_unit_ids|[](ID)|选择改动\nexpected_workspace_version|Version|当前基线","MergeResult","workspace_write",["撤销创建新版本；用户后续编辑不覆盖；外部服务动作不属于文件撤销。"],feature="file_write")
endpoint("processes.get","GET","/v1/processes/{process_id}","workspace","ui workspace.process","进程状态/日志。","process_id|ID|进程\ncursor?|Cursor|增量","ProcessRecord",feature="process_exec")
endpoint("processes.stop","POST","/v1/processes/{process_id}/stop","workspace","workspace.process run.cancel","停止进程树。","process_id|ID|进程\nreason|NonEmptyText|理由","ProcessRecord","process",["先软终止、超时硬终止；离线lost不伪称stopped。"],feature="process_exec")
endpoint("artifacts.list","GET","/v1/tasks/{task_id}/artifacts","workspace","ui workspace.artifacts","成果列表。","task_id|ID|任务\ncursor?|Cursor|续页\nlimit?|PageLimit|页大小","ArtifactPage")
endpoint("artifacts.get","GET","/v1/artifacts/{artifact_id}","workspace","ui workspace.artifacts","成果版本。","artifact_id|ID|成果\nversion?|Version|不指定返回当前版本","ArtifactRecord")
endpoint("artifacts.preview","POST","/v1/artifacts/{artifact_id}/preview","workspace","ui workspace.artifacts","生成安全预览入口。","artifact_id|ID|成果\nversion|Version|固定版本","DownloadTicket",rules=["HTML预览在独立安全域，禁主动外部副作用；无预览适配器返回unsupported_format。"])
endpoint("artifacts.export","POST","/v1/artifacts/{artifact_id}/export","workspace","workspace.artifacts","导出固定版本。","artifact_id|ID|成果\nversion|Version|版本\nformat_kind|NonEmptyText|批准格式","DownloadTicket",rules=["内容转换派生成新成果，保留来源；不能谎称原版本验证适用于转换后版本。"])
endpoint("reviews.get","GET","/v1/reviews/{review_id}","workspace","ui workspace.review","查看审阅。","review_id|ID|审阅","ReviewSet")
endpoint("reviews.decide","POST","/v1/reviews/{review_id}/decisions","workspace","ui workspace.review agent.completion.acceptance","接受/反馈。","review_id|ID|审阅\ndecision|ReviewDecision|用户决定","ReviewSet","internal_write",["expected_revision与成果基线双校验；接受意见不会偷偷执行文件合并，应用改动需显式merge。"])
endpoint("verification.get","GET","/v1/verifications/{verification_id}","agent","ui agent.completion.semantic","查看核验报告。","verification_id|ID|报告","VerificationReport")
endpoint("models.list","GET","/v1/models","model","ui model.catalog","用户可用模型目录。","cursor?|Cursor|续页\nlimit?|PageLimit|页大小","ModelPage")
endpoint("connections.list","GET","/v1/connections","support","support.configuration","私人账号连接。","cursor?|Cursor|续页\nlimit?|PageLimit|页大小","ConnectionPage",rules=["HTTP普通用户视图不含credential_ref；模式关闭凭据字段。"])
endpoint("connections.begin","POST","/v1/connections","support","support.configuration tool.mcp.provider","开始外部账号授权。","provider_ref|Ref|管理员登记服务\nrequested_scopes|[](ID)|授权范围","AuthorizationStart","credential")
record("AuthorizationStart","support","带state和PKCE的授权事务；OAuth回调由特定提供方适配器验证。","connection_id|ID|连接\nauthorization_url|URL|外部授权入口\nexpires_at|Timestamp|截止")
endpoint("connections.revoke","DELETE","/v1/connections/{connection_id}","support","support.configuration tool.mcp.invalidate","撤销连接。","connection_id|ID|连接","DeletionReceipt","credential",["能力索引与session立即失效，旧审批不可继续使用。"])
endpoint("admin.configuration.get","GET","/v1/admin/configuration","support","support.configuration","有效配置。","","ConfigurationVersion",auth="admin")
endpoint("admin.configuration.stage","POST","/v1/admin/configuration/drafts","support","support.configuration","创建待验证配置。","configuration|ConfigurationVersion|非秘密配置","ConfigurationVersion","internal_write",["revision/主体由服务决定；秘密另经secret write-only接口。"],auth="admin")
endpoint("admin.configuration.validate","POST","/v1/admin/configuration/drafts/{configuration_id}/validate","support","support.configuration model.catalog tool.registry","验证目录与适配器。","configuration_id|ID|草案","ValidationReport",auth="admin")
endpoint("admin.configuration.activate","POST","/v1/admin/configuration/drafts/{configuration_id}/activate","support","support.configuration","原子发布配置。","configuration_id|ID|已验证草案","ConfigurationVersion","internal_write",["expected_revision；受影响发现索引和缓存失效，旧在途调用固定旧配置并受撤销闸门控制。"],auth="admin")
endpoint("admin.tools.register","POST","/v1/admin/tools","tool","tool.registry","注册工具schema与提供方。","spec|ToolSpec|工具版本","ToolSpec","internal_write",["检查schema合法、唯一版本、提供方可用；向量索引异步构建且保持目录版本一致。"],auth="admin")
endpoint("admin.tools.list","GET","/v1/admin/tools","tool","tool.registry","管理工具版本。","cursor?|Cursor|续页\nlimit?|PageLimit|页大小","ToolPage",auth="admin")
endpoint("admin.models.register","POST","/v1/admin/models","model","model.catalog","登记模型能力。","entry|ModelCatalogEntry|模型契约","ModelCatalogEntry","internal_write",auth="admin")
endpoint("admin.providers.configure","POST","/v1/admin/providers","support","support.configuration tool.mcp.provider model.adapters","登记非秘密服务配置。","provider|ProviderDraft|批准的提供方参数","ProviderBinding","internal_write",auth="admin")
record("ProviderDraft","support","提供方类型对应的配置须通过profile schema，不能带明文secret。","id|ID|提供方\nkind|ProviderKind|类型\nendpoint|URL|管理员批准地址\nprofile_ref|Ref|适配器配置schema\nsettings|Object|按profile额外校验\ncredential_handle?|ID|凭据库句柄")
endpoint("admin.secrets.put","POST","/v1/admin/secrets","support","support.configuration","仅管理端TLS写入秘密，不回显不记录正文。","provider_id|ID|目标提供方\nsecret|SecretValue|待加密值","SecretReceipt","credential",["日志/缓存/trace禁止记录secret；前端与模型不可读取秘密。"],auth="admin")
scalar("SecretValue","support","write-only秘密，最大8192字符。",type="string",minLength=1,maxLength=8192,writeOnly=True)
record("SecretReceipt","support","只返回句柄。","credential_handle|ID|秘密句柄\nversion|Version|秘密版本")
endpoint("admin.environments.register","POST","/v1/admin/environments","workspace","workspace.environment","登记初始化模板。","template|EnvironmentTemplate|环境模板","EnvironmentTemplate","internal_write",auth="admin")
endpoint("admin.extensions.install","POST","/v1/admin/extensions","support","support.extensions","安装能力包。","bundle_ref|Ref|已上传包\nmanifest|ExtensionManifest|依赖声明","ExtensionManifest","internal_write",["哈希、依赖和能力验证；install不等于activate。"],auth="admin",feature="extensions")
endpoint("admin.extensions.activate","POST","/v1/admin/extensions/{extension_id}/activate","support","support.extensions","激活包。","extension_id|ID|插件","ExtensionManifest","internal_write",auth="admin",feature="extensions")
endpoint("admin.extensions.revoke","DELETE","/v1/admin/extensions/{extension_id}","support","support.extensions tool.mcp.invalidate","撤销/停用包。","extension_id|ID|插件","DeletionReceipt","internal_write",auth="admin",feature="extensions")
endpoint("admin.extensions.validate","POST","/v1/admin/extensions/{extension_id}/validate","support","support.extensions","核验安装包、依赖和权限需求。","extension_id|ID|插件","ValidationReport",auth="admin",feature="extensions")
endpoint("admin.extensions.rollback","POST","/v1/admin/extensions/{extension_id}/rollback","support","support.extensions","恢复已核验旧包为新配置修订。","extension_id|ID|插件\ntarget_version_ref|Ref|旧固定版本","ExtensionManifest","internal_write",["CAS；旧包仍须安全/依赖有效；不回滚外部动作；撤销与新实例策略当前生效。"],auth="admin",feature="extensions")
endpoint("admin.policies.register","POST","/v1/admin/policies","support","support.configuration run.approval support.cache","登记有类型政策。","draft|PolicyDraft|政策草案","Ref","internal_write",["校验后登记但不立即激活；须configuration.activate引用该版本。"],auth="admin")
endpoint("admin.traces.list","GET","/v1/admin/traces/{trace_id}","support","support.observability","脱敏诊断。","trace_id|ID|链路\ncursor?|Cursor|续页\nlimit?|PageLimit|页大小","TracePage",auth="admin")
endpoint("admin.evaluations.run","POST","/v1/admin/evaluations","support","support.evaluation","固定样本评测。","candidate_manifest|Ref|候选\nbaseline_manifest|Ref|基线\ndataset_version|Ref|样本\nfixture_environment|Ref|环境\ngrader_config|Ref|评分配置","EvaluationResult","internal_write",auth="admin")
endpoint("admin.evaluations.get","GET","/v1/admin/evaluations/{evaluation_id}","support","support.evaluation","读取评测结果；未完成返回waiting及作业Ref。","evaluation_id|ID|评测","EvaluationResult",auth="admin")
endpoint("triggers.create","POST","/v1/tasks/{task_id}/triggers","run","run.trigger","定时触发，默认旗标可关闭。","task_id|ID|任务\nschedule|NonEmptyText|时间规则\ntimezone|NonEmptyText|IANA时区\noverlap_policy|OverlapPolicy|重叠","TriggerSpec","internal_write",feature="automations")
endpoint("triggers.disable","DELETE","/v1/triggers/{trigger_id}","run","run.trigger","关闭触发器。","trigger_id|ID|触发器","Acknowledgement","internal_write",feature="automations")

# LLM control/operational tools: current conversation/run supplied by Tool Runtime.
tool("tools.discover","tool","tool.discovery agent.definitions.discovery","按语义寻找当前可用工具和角色。","query|NonEmptyText|任务相关搜索\ncategories?|[](ID)|收窄类别\nmax_candidates|CandidateLimit|最多候选","DiscoveryResult",rules=["角色类别、产品旗标和权限先过滤，混合召回后交当前LLM选；小目录可直接返回。"])
scalar("CandidateLimit","tool","一次候选数量。",type="integer",minimum=1,maximum=32)
tool("context.read","context","context.sources context.references","读取当前授权资料。","references|[](Ref)|已知引用\nlocation?|Location|位置\ncursor?|Cursor|下一页","ReadResult")
tool("skills.load","agent","agent.skills context.rules","加载获准技能方法。","skill_ref|Ref|技能版本","SkillSpec",rules=["加载不自动运行脚本；依赖能力仍经Tool Runtime。"])
tool("agents.create","agent","agent.definitions agent.definitions.designer agent.definitions.validator agent.definitions.model_intent agent.definitions.repository","把用户明确要求的子Agent保存到当前会话。","definitions|DefinitionDrafts|草案\nbatch_policy|BatchPolicy|批量策略\nsource_input_ref|Ref|明确用户要求","DefinitionBatchResult","internal_write",["不能包含owner、权限批准或conversation；create不启动实例；同键相同内容幂等。"])
tool("agents.update","agent","agent.definitions.change_service agent.definitions.validator","更新当前会话角色。","definition_id|ID|角色\nexpected_revision|Revision|定义CAS版本\npatch|DefinitionPatch|修改\nsource_input_ref|Ref|用户依据","AgentDefinitionVersion","internal_write")
tool("agents.list","agent","agent.definitions.discovery","发现会话中可复用角色。","query?|NonEmptyText|任务相关筛选\nmax_candidates|CandidateLimit|最多摘要","CandidatePage")
tool("agents.invoke","agent","agent.assessment agent.collaboration.contract agent.factory agent.collaboration.instance","创建隔离实例执行当前有界分工。","delegation|DelegationSpec|目标、资料、成果、预算","AgentInstance","internal_write",["调用是当前主Agent语义决定；创建角色不自动invoke；不做独立性成立不了的并发。"])
tool("agents.wait","agent","agent.collaboration.channel agent.collaboration.join","等待子Agent结果或需要注意。","agent_refs|WaitTargets|最多8个实例\ncursor?|Cursor|增量\nwait_ms|WaitDuration|等待时间","AgentWaitResult")
scalar("WaitTargets","agent","等待最多8个。",type="array",items=ref("Ref"),minItems=1,maxItems=8,uniqueItems=True)
scalar("WaitDuration","common","0立即状态查询，最多60秒。",type="integer",minimum=0,maximum=60000)
tool("agents.message","agent","agent.collaboration.channel","向当前任务的子Agent发送协作资料。","to_agent_ref|Ref|接收实例\nmessage_id|ID|去重键\ntext|Text|信息\npayload_refs|[](Ref)|获准资料","AgentMessage","internal_write",["实例树内授权；不能向不相关用户会话发送消息。"])
tool("agents.cancel","agent","agent.collaboration.cancel run.cancel","停止当前实例子树。","agent_ref|Ref|子树根\nreason|NonEmptyText|理由","CancellationResult","internal_write")
tool("agents.handoff","agent","agent.collaboration.handoff","显式移交任务控制权。","to_agent_ref|Ref|新控制者\nexpected_control_revision|Revision|控制版本\nunfinished_refs|[](Ref)|未完工作","ControlLease","internal_write",["CAS交换租约；原控制者丢失栅栏不能再提交；不可移交未确认外部副作用。"],feature="agent_handoff")
tool("tasks.assess","agent","agent.assessment","按语义与实际能力判断执行规模。","task_frame_ref|Ref|理解版本\ndecision_question?|Text|需要重评的问题","ExecutionAssessment",rules=["默认单Agent；独立评估规划、委派、并发；额外工作须预算内有收益。"])
tool("tasks.plan","agent","agent.planning agent.scheduler","创建/修改执行计划。","planning_level|GraphPlanningLevel|steps或dag\nnode_specs|[](NodeSpec)|完整初始图\npatch?|PlanPatch|增量修改\nexpected_plan_revision|Revision|0创建","TaskGraph","internal_write",["patch与非空node_specs互斥；硬依赖校验由代码；不自动invoke。"])
enum("GraphPlanningLevel","steps|dag","agent")
tool("tasks.verify","agent","agent.completion.contract agent.completion.evidence agent.completion.semantic agent.completion.version","语义完成校验。","contract_ref|Ref|验收\nartifact_refs|[](Ref)|成果\nevidence_refs|[](Ref)|证据","VerificationReport",rules=["缺测试只能not_run/blocked，不能按模型陈述passed；返回报告不自动完成Run。"])
tool("models.list","model","model.catalog","查询用户可用模型，以处理用户明确指定名。","required_capabilities?|[](ID)|必要协议","ModelPage")
tool("workspace.changes","workspace","workspace.changes","查看实际文件改动。","workspace_ref|Ref|工作区","ChangeSet")
tool("workspace.revert","workspace","workspace.changes","撤销选定可逆文件改动。","workspace_ref|Ref|目标版本\nchange_set_ref|Ref|变更\nselected_unit_ids|[](ID)|改动块\nexpected_workspace_version|Version|当前基线","MergeResult","workspace_write",feature="file_write")
tool("references.resolve","context","context.references","解析实际引用。","reference|Ref|目标","ResolvedReference")
tool("references.read","context","context.references","读取资料位置。","reference|Ref|固定版本\nlocation?|Location|位置\ncursor?|Cursor|分页","ReadResult")
tool("environment.inspect","workspace","workspace.environment","检查真实语言与依赖。","workspace_ref|Ref|工作区","EnvironmentRecord",feature="process_exec")
tool("environment.ensure","workspace","workspace.environment","按批准模板准备环境并核验。","workspace_ref|Ref|工作区\ntemplate_ref|Ref|批准模板","EnvironmentRecord","process",["预装优先，安装受权限/网络来源/预算约束；失败返回真实日志；cwd和venv不等于OS隔离。"],feature="environment_install")
tool("process.exec","workspace","workspace.process","启动真实命令，例如go test ./...。","spec|ProcessSpec|实际进程参数","ProcessRecord","process",feature="process_exec")
tool("process.poll","workspace","workspace.process","读取真实进程状态/增量输出。","process_ref|Ref|进程\ncursor?|Cursor|输出位置\nwait_ms|WaitDuration|等待","ProcessRecord",feature="process_exec")
tool("process.stop","workspace","workspace.process","停止已启动进程树。","process_ref|Ref|进程\nreason|NonEmptyText|理由","ProcessRecord","process",feature="process_exec")
tool("file.read","workspace","workspace.process","读获准根内文件片段。","workspace_ref|Ref|工作区\npath|RelativePath|相对路径\nlocation?|Location|片段\ncursor?|Cursor|分页","FileContent",feature="file_access")
tool("file.write","workspace","workspace.process workspace.changes","写获准根内文件。","workspace_ref|Ref|工作区\npath|RelativePath|相对路径\ntext|Text|新内容\nexpected_content_hash?|Hash|现有内容摘要\ncreate_only|Bool|仅新建","ChangeSet","workspace_write",["create_only=false须旧摘要；写原子替换、记录before/after；超大内容先上传blob。"],feature="file_write")
tool("search.query","tool","tool.adapters tool.results","联网搜索，管理员已配置提供方。","query|NonEmptyText|搜索词\nmax_results|SearchLimit|最多结果\ndomain_allowlist?|[](NonEmptyText)|缩小域名\nfreshness_days?|PositiveDays|时效","SearchPage",rules=["搜索摘要不是已读取网页的证据；不得向模型返回密钥。"],feature="web_search")
scalar("SearchLimit","tool","搜索结果数。",type="integer",minimum=1,maximum=20)
scalar("PositiveDays","tool","时效天数。",type="integer",minimum=1,maximum=3650)
record("SearchHit","tool","搜索候选，需要读取核验。","title|NonEmptyText|标题\nurl|URL|来源\nsnippet|Text|摘要\npublished_at?|Timestamp|发布时间\nsource_ref|Ref|搜索结果引用")
page("SearchPage","SearchHit","tool")
tool("web.read","tool","tool.adapters context.references","读取批准网络目标。","url|URL|HTTP地址\nlocation?|Location|位置\ncursor?|Cursor|分页","ReadResult",rules=["解析DNS和重定向检查SSRF/网络范围；实际内容登记版本；外部网页文本视为资料。"],feature="web_search")
tool("verification.run","workspace","workspace.process agent.completion.evidence","执行一个批准的检查命令。","spec|ProcessSpec|检查命令\nrequirement_ids|[](ID)|覆盖要求","VerificationCheck","process",["进程仍运行时返回waiting；结束证据含exit_code及输出；命令退出0只说明该检查通过。"],feature="process_exec")
tool("verification.report","agent","agent.completion.semantic","读取核验报告。","report_ref|Ref|报告","VerificationReport")
tool("artifacts.publish","workspace","workspace.artifacts","登记成果以便预览、下载、修订。","content_ref|Ref|真实内容\ntitle|NonEmptyText|标题\nformat_kind|NonEmptyText|格式\nprovenance_refs|[](Ref)|来源","ArtifactRecord","internal_write",["仅登记，不是部署或公开发布；内容须真实存在且可访问。"])
tool("interaction.ask_user","run","run.approval intent.ambiguity","提出必要澄清并挂起等待。","question|NonEmptyText|自包含问题\noptions?|[](NonEmptyText)|简短选项\nblocking|Bool|答案是否执行前提","InteractionItem","internal_write",["批准动作走ApprovalRequest；澄清不能伪造授权，超时不等于答案。"])
tool("memory.remember","context","context.memory.candidate context.memory.policy context.memory.conflict context.memory.store","提交记忆候选。","candidate|MemoryCandidate|来源及范围","MemoryRecord","internal_write")
tool("memory.recall","context","context.memory.store","按政策读取记忆。","selector|MemorySelector|筛选\nquery?|NonEmptyText|语义检索","MemoryPage")
tool("memory.forget","context","context.memory.forget","删除授权范围记忆。","selector|MemorySelector|明确非空选择","DeletionReceipt","internal_write")

# Runtime facade: explicit internal signatures with injected TrustedExecutionContext.
record("UnderstandingRequest","intent","首次理解，可复用主Agent同次输出。","original_input_ref|Ref|原文\nuser_patch_refs|[](Ref)|补充\nmaterial_refs|[](Ref)|资料\nexpected_revision|Revision|理解CAS")
record("FramePatchRequest","intent","用户修订后的新理解。","current_frame_ref|Ref|旧版本\nnew_input_ref|Ref|新要求\nexpected_revision|Revision|CAS")
record("ContextRequest","context","统一上下文构建入口，purpose决定启用哪些策略。","purpose|Purpose|目的\nsource_refs|[](Ref)|来源\nmodel_policy_ref|Ref|当前模型\noutput_reserve|Count|输出预留\ntool_reserve|Count|工具预留\npreserve|PreservationSpec|保护要求\nexpected_epoch|Revision|上下文纪元")
record("ModelCall","model","统一模型调用。","context_snapshot_ref|Ref|快照\nmodel_config|ResolvedModelConfig|真实配置\noutput_protocol|Protocol|结果协议\noutput_schema?|Schema|json_schema时必需\nattempt_id|ID|尝试")
record("WorkspaceSpec","workspace","统一工作区分配。","base_ref|Ref|基础状态\nmode|IsolationMode|隔离\nwriter_agent_ref|Ref|写实例\nproject_binding_ref?|Ref|设备绑定")
record("AgentStartRequest","agent","创建根执行实例。","run_ref|Ref|当前运行\ntask_frame_ref|Ref|理解\ncreation_key|ID|去重键\nrole_profile_ref?|Ref|默认角色")
record("AgentStepRequest","agent","单次推进循环，调度器不越过LLM决策。","instance_ref|Ref|固定实例\nobservations|[](Ref)|新增结果\ncurrent_frame_ref|Ref|当前理解\nremaining_budget|Budget|可用预算")
record("AgentStepResult","agent","每步建议下一动作，由硬闸门确认。","action|AgentStepAction|下一动作\nmodel_output_ref|Ref|模型依据\nproposed_calls|[](ToolCall)|工具建议\ncompletion_proposal_ref?|Ref|完成提案\ninstance_ref|Ref|提交后实例")
enum("AgentStepAction","respond|call_tools|wait|propose_completion|blocked","agent")
record("ReconcileRequest","tool","针对未知效果查回执，先查后恢复。","action_id|ID|动作\nexpected_revision|Revision|账本CAS")
record("RunCreateRequest","run","原文入库与Run受理原子关联。","conversation_id|ID|会话\ninput|InputRecord|用户输入\ntask_ref?|Ref|已有任务\nbudget|Budget|上限")
record("RunControlRequest","run","内部控制入口。","run_ref|Ref|运行\ncontrol|UserControl|方式\nexpected_revision|Revision|CAS")
for id,owner,nodes,req,res,effect,rules in [
 ("IntentRuntime.preview","intent","intent intent.preview","IntentPreviewRequest","DraftPreview","read",["预览只读，不创建正式任务。"]),
 ("IntentRuntime.understand","intent","intent intent.original intent.semantic intent.frame","UnderstandingRequest","TaskFrame","internal_write",[]),
 ("IntentRuntime.revise","intent","intent intent.frame","FramePatchRequest","TaskFrame","internal_write",[]),
 ("AgentRuntime.define_agent","agent","agent agent.definitions","ToolAgentsCreateInput","DefinitionBatchResult","internal_write",[]),
 ("AgentRuntime.start","agent","agent agent.factory","AgentStartRequest","AgentInstance","internal_write",[]),
 ("AgentRuntime.step","agent","agent agent.loop","AgentStepRequest","AgentStepResult","internal_write",[]),
 ("AgentRuntime.delegate","agent","agent agent.collaboration","DelegationSpec","AgentInstance","internal_write",[]),
 ("AgentRuntime.verify","agent","agent agent.completion","ToolTasksVerifyInput","VerificationReport","read",[]),
 ("ContextRuntime.build","context","context context.composer","ContextRequest","ContextSnapshot","read",[]),
 ("ContextRuntime.ingest","context","context context.ingestion","SourcesIngestRequest","IngestionRecord","internal_write",[]),
 ("ContextRuntime.remember","context","context context.memory","MemoryCandidate","MemoryRecord","internal_write",[]),
 ("ContextRuntime.recall","context","context context.memory","ToolMemoryRecallInput","MemoryPage","read",[]),
 ("ContextRuntime.forget","context","context context.memory.forget","MemorySelector","DeletionReceipt","internal_write",[]),
 ("ContextRuntime.resolve_reference","context","context context.references","RefRequest","ResolvedReference","read",[]),
 ("ToolRuntime.discover","tool","tool tool.discovery","ToolToolsDiscoverInput","DiscoveryResult","read",[]),
 ("ToolRuntime.invoke","tool","tool tool.invocation","ToolCall","ToolResult","external_write",["effect由固定ToolSpec确定，不由调用者指定；本描述是最大风险上限。"]),
 ("ToolRuntime.reconcile","tool","tool tool.effects","ReconcileRequest","EffectRecord","read",[]),
 ("WorkspaceRuntime.allocate","workspace","workspace workspace.isolation","WorkspaceSpec","WorkspaceRecord","internal_write",[]),
 ("WorkspaceRuntime.prepare","workspace","workspace workspace.environment","ToolEnvironmentEnsureInput","EnvironmentRecord","process",[]),
 ("WorkspaceRuntime.merge","workspace","workspace workspace.changes","WorkspacesMergeRequest","MergeResult","workspace_write",[]),
 ("WorkspaceRuntime.revert","workspace","workspace workspace.changes","WorkspacesRevertRequest","MergeResult","workspace_write",[]),
 ("WorkspaceRuntime.review","workspace","workspace workspace.review","ReviewsDecideRequest","ReviewSet","internal_write",[]),
 ("ModelRuntime.resolve_policy","model","model model.policy","ModelPolicyRequest","ResolvedModelPolicy","read",[]),
 ("ModelRuntime.list","model","model model.catalog","ToolModelsListInput","ModelPage","read",[]),
 ("ModelRuntime.generate","model","model model.gateway","ModelCall","ModelOutput","read",[]),
 ("RunRuntime.create","run","run run.history run.state","RunCreateRequest","RunRecord","internal_write",[]),
 ("RunRuntime.control","run","run run.approval run.cancel","RunControlRequest","Acknowledgement","internal_write",[]),
 ("RunRuntime.checkpoint","run","run run.checkpoint","RunsCheckpointRequest","Checkpoint","internal_write",[]),
 ("RunRuntime.resume","run","run run.resume","RunsResumeRequest","RunRecord","internal_write",[]),
 ]: facade(id,owner,nodes,req,res,effect,rules)
record("ModelPolicyRequest","model","模型政策必须来自明确用户意图或父政策。","conversation_selection|ModelSelection|会话已记录意图\nparent_policy_ref?|Ref|父政策\nexplicit_child_request?|ModelRequest|子覆盖\nuser_source_ref|Ref|真实用户依据")

# Runner transport operations: device bearer token + command signature, local rechecks.
def runner(id,nodes,description,spec,response,effect="read",rules=()):
    name="Runner"+"".join(x.capitalize() for x in id.split("."))+"Request"
    record(name,"workspace",description,spec,rules)
    operation(id,"runner","workspace",nodes,name,response,effect,rules,auth="runner")
runner("pair.begin","workspace.binding","本机用户启动配对。","device_nonce|ID|一次随机标识\ndisplay_name|NonEmptyText|本机名称\ncapabilities|[](ID)|实际能力","RunnerPairing","credential",["未配对无项目访问权；一次码只经用户账户页面确认。"])
runner("pair.complete","workspace.binding","完成配对，绑定当前设备。","pairing_id|ID|事务\nverification_code|NonEmptyText|一次码\ndevice_public_key|NonEmptyText|设备公钥","RunnerDevice","credential")
runner("heartbeat","workspace.binding","在线状态与租约维护。","device_id|ID|设备\nrevision|Revision|设备版本\nactive_process_refs|[](Ref)|存活进程\nactive_lease_refs|[](Ref)|租约","RunnerDevice")
runner("root.select","workspace.binding","本机可信目录选择，产生短期凭据。","native_path|Path|用户本机选择\nrequested_capabilities|[](ID)|read/write/exec","RootSelection","credential",["native_path绝不接受模型提供；realpath校验并由本机交互确认。"])
record("RootSelection","workspace","本机选择证明，网页绑定不拿明文根目录。","selection_token|NonEmptyText|短期签名一次凭据\ndisplay_name|NonEmptyText|名称\nexpires_at|Timestamp|期限\nroot_handle|ID|本地句柄")
for id,nodes,request,response,effect in [
 ("workspace.capture","workspace.base","CaptureRequest","BaseState","read"),
 ("workspace.allocate","workspace.isolation","WorkspaceSpec","WorkspaceRecord","internal_write"),
 ("environment.inspect","workspace.environment","ToolEnvironmentInspectInput","EnvironmentRecord","read"),
 ("environment.ensure","workspace.environment","ToolEnvironmentEnsureInput","EnvironmentRecord","process"),
 ("file.read","workspace.process","ToolFileReadInput","FileContent","read"),
 ("file.write","workspace.process workspace.changes","ToolFileWriteInput","ChangeSet","workspace_write"),
 ("file.list","workspace.process","WorkspacesFilesRequest","FilePage","read"),
 ("process.exec","workspace.process","ToolProcessExecInput","ProcessRecord","process"),
 ("process.poll","workspace.process","ToolProcessPollInput","ProcessRecord","read"),
 ("process.stop","workspace.process","ToolProcessStopInput","ProcessRecord","process"),
 ("changes.capture","workspace.changes","ToolWorkspaceChangesInput","ChangeSet","read"),
 ("changes.merge","workspace.changes","WorkspacesMergeRequest","MergeResult","workspace_write"),
 ("changes.revert","workspace.changes","WorkspacesRevertRequest","MergeResult","workspace_write"),
 ("workspace.release","workspace.isolation workspace.environment","RefRequest","Acknowledgement","internal_write"),
 ]: operation(id,"runner","workspace",nodes,request,response,effect,["网络请求实际为RunnerCommand信封，签名/期限/主体/根/栅栏与业务参数均复核；重复command_id只返回原执行状态。"],auth="runner")
record("CaptureRequest","workspace","真实采集获准输入状态。","source_ref|Ref|项目/提交\nbase_kind|BaseKind|提交或目录\ninclude_rules|IncludeRules|收录\nexpected_source_revision|Version|基础版本")

# Additional private stage outputs; no untyped catch-all result.
record("SourceBundle","context","访问过滤并固定来源版本。","source_refs|[](Ref)|有效来源\nmissing_refs|[](Ref)|明确缺口\nmanifest|Manifest|依赖")
record("SemanticParse","intent","解析是有来源的候选，后续frame提交须CAS。","interpretations|[](Interpretation)|候选\nrequirements|[](Requirement)|要求\noutput_specs|[](OutputSpec)|成果\nsource_refs|[](Ref)|来源")
record("ProbeResult","intent","有界只读探查结果。","evidence_refs|[](Ref)|读取证据\nunresolved|[](NonEmptyText)|缺口\nusage_ref|Ref|实际消耗")
record("AmbiguityDecision","intent","可逆低影响假设显式记录，高影响缺口先澄清。","selected?|Interpretation|可执行理解\nquestion_item_ref?|Ref|待用户回答\nassumptions|[](NonEmptyText)|采用假设")
record("SelectionResult","context","预算分配与遗漏有据可查。","selected_refs|[](Ref)|选取内容\nomitted_refs|[](Ref)|裁剪\nallocated_tokens|Count|预算\npreserved_refs|[](Ref)|保护")
record("CompressionResult","context","压缩派生摘要附保留核验。","summary_ref|Ref|结果\nsource_snapshot_ref|Ref|源\npreservation_report_ref|Ref|关键要素核验\noutput_tokens|Count|摘要估算Token")
record("MemoryPolicyDecision","context","记忆政策判定不是LLM自批。","allowed|Bool|是否允许\neffective_scope|Scope|最终范围\nexpires_at?|Timestamp|期限\nreason|NonEmptyText|依据")
record("MemoryConflictDecision","context","互斥事实不能简单拼接。","action|MemoryConflictAction|新增/更新/澄清/拒绝\ncandidate_ref|Ref|候选\nconflicting_refs|[](Ref)|冲突\nreason|NonEmptyText|依据")
enum("MemoryConflictAction","insert|supersede|clarify|reject","context")
record("ValidatedCall","tool","参数schema通过的固定工具版本。","tool_ref|Ref|固定契约\narguments|Object|规范参数\narguments_hash|Hash|规范摘要\naction_id|ID|动作")
record("PrecheckDecision","tool","调用前范围、旗标和预算判定。","allowed|Bool|可否继续\napproval_required|Bool|是否审批\npolicy_ref|Ref|有效政策\nresource_refs|[](Ref)|实际基线\nreservation_ref?|Ref|已预留资源\nviolations|[](ValidationIssue)|阻碍")
record("RecheckDecision","tool","审批后再次核对参数/资源/权限。","allowed|Bool|是否仍允许\nvalidated_call_ref|Ref|调用\nresource_refs|[](Ref)|最新匹配资源\napproval_ref?|Ref|授权\nreason|NonEmptyText|依据")
record("ProviderReceipt","tool","适配器原始结果指针，业务语义交规范器。","attempt_id|ID|实际尝试\nraw_result_ref|Ref|原始响应\ntransport_status|NonEmptyText|传输状态\neffect_state|EffectState|效果确定性\nusage|Usage|实际用量")
record("UsageSettlement","model","预留结算重复回执不得重复计费。","reservation_ref|Ref|预留\nusage_refs|[](Ref)|所有attempt\nremaining|ResourceVector|剩余\nrevision|Revision|账本版本\nbilling_pending|Bool|是否待账单")
record("CapabilityCheck","model","固定模型不支持能力须报错，Auto只能在授权候选中选。","supported|Bool|满足\nconfig?|ResolvedModelConfig|可执行配置\nmissing_capabilities|[](ID)|缺能力\nreason|NonEmptyText|依据")
record("ResumeAccessResult","run","恢复按当前权限，不按旧快照复活权限。","authorized_refs|[](Ref)|仍获准资源\nunavailable_refs|[](Ref)|撤销/删除/断连\nconfiguration_ref|Ref|当前配置\nblocking_reasons|[](NonEmptyText)|阻碍")
record("ResumeEffectsResult","run","未确定效果阻止相关节点重放。","confirmed_refs|[](Ref)|已对账\nunknown_refs|[](Ref)|仍未知\nretryable_action_refs|[](Ref)|可安全恢复动作")
record("RepositoryReceipt","support","仓储CAS回执。","resource_ref|Ref|资源\nrevision|Revision|提交版本\nunchanged|Bool|幂等命中")

# Internal-only stages. Original design payloads are expanded into named schemas.
# Branches reuse public DTOs only when meanings match; trust is always separate.
COMPONENT_OUTPUTS={
 "ui":"InteractionItem","ingress":"RunRecord",
 "intent.preview":"DraftPreview","intent.original":"InputRecord","intent.semantic":"SemanticParse",
 "intent.references":"SourceBundle","intent.probe":"ProbeResult","intent.ambiguity":"AmbiguityDecision","intent.frame":"TaskFrame",
 "agent.definitions":"DefinitionBatchResult","agent.loop":"AgentStepResult","agent.assessment":"ExecutionAssessment",
 "agent.planning":"TaskGraph","agent.scheduler":"SchedulerResult","agent.collaboration":"AgentInstance",
 "agent.skills":"SkillSpec","agent.completion":"DeliveryProposal","agent.board":"BoardEntry","agent.factory":"AgentInstance",
 "agent.definitions.designer":"AgentDefinitionDraft","agent.definitions.validator":"ValidationReport",
 "agent.definitions.model_intent":"ResolvedModelPolicy","agent.definitions.repository":"DefinitionBatchResult",
 "agent.definitions.discovery":"CandidatePage","agent.definitions.change_service":"DefinitionDiff",
 "context.sources":"SourceBundle","context.rules":"InstructionSet","context.ingestion":"IngestionRecord",
 "context.retrieval":"RetrievalPage","context.memory":"MemoryRecord","context.selection":"SelectionResult",
 "context.compression":"CompressionResult","context.composer":"ContextSnapshot","context.references":"ReferenceRecord",
 "tool.registry":"ToolSpec","tool.discovery":"DiscoveryResult","tool.invocation":"ToolResult","tool.effects":"EffectRecord",
 "tool.failure":"RecoveryDecision","tool.mcp":"McpSession","tool.adapters":"ProviderReceipt","tool.results":"ToolResult","tool.audit":"AuditRecord",
 "workspace.binding":"ProjectBinding","workspace.base":"BaseState","workspace.isolation":"WorkspaceRecord",
 "workspace.environment":"EnvironmentRecord","workspace.process":"ProcessRecord","workspace.changes":"MergeResult",
 "workspace.artifacts":"ArtifactRecord","workspace.review":"ReviewSet",
 "model.catalog":"ModelPage","model.policy":"ResolvedModelPolicy","model.capability":"CapabilityCheck",
 "model.gateway":"ModelOutput","model.adapters":"ProviderReceipt","model.recovery":"RecoveryDecision","model.usage":"UsageSettlement",
 "run.history":"InputRecord","run.state":"RunRecord","run.events":"EventEnvelope","run.budget":"BudgetReservation",
 "run.approval":"ApprovalRequest","run.checkpoint":"Checkpoint","run.resume":"RunRecord","run.cancel":"CancellationResult","run.trigger":"RunRecord",
 "support.configuration":"ConfigurationVersion","support.extensions":"ExtensionManifest","support.cache":"CacheLookupResult",
 "support.observability":"TraceSpan","support.evaluation":"EvaluationResult","support.stores":"RepositoryReceipt",
 "tool.invocation.schema":"ValidatedCall","tool.invocation.precheck":"PrecheckDecision","tool.invocation.approval":"ApprovalRequest",
 "tool.invocation.recheck":"RecheckDecision","tool.invocation.dispatch":"ProviderReceipt","tool.invocation.result":"ToolResult",
 "agent.collaboration.contract":"DelegationSpec","agent.collaboration.instance":"AgentInstance","agent.collaboration.channel":"AgentMessage",
 "agent.collaboration.join":"AgentResult","agent.collaboration.handoff":"ControlLease","agent.collaboration.cancel":"CancellationResult",
 "agent.completion.contract":"Contract","agent.completion.evidence":"CheckPage","agent.completion.semantic":"VerificationReport",
 "agent.completion.version":"ValidationReport","agent.completion.delivery":"RunRecord","agent.completion.acceptance":"ReviewSet",
 "context.memory.candidate":"MemoryCandidate","context.memory.policy":"MemoryPolicyDecision","context.memory.conflict":"MemoryConflictDecision",
 "context.memory.store":"MemoryRecord","context.memory.forget":"DeletionReceipt",
 "tool.mcp.provider":"ProviderBinding","tool.mcp.session":"McpSession","tool.mcp.capabilities":"ToolPage",
 "tool.mcp.invoke":"ProviderReceipt","tool.mcp.invalidate":"Acknowledgement",
 "run.resume.lease":"ControlLease","run.resume.versions":"CompatibilityReport","run.resume.access":"ResumeAccessResult",
 "run.resume.effects":"ResumeEffectsResult","run.resume.workspace":"CompatibilityReport","run.resume.continue":"RunRecord",
}

# Multi-action components use an explicit tagged union. Each branch has its own
# schema, so `read` never incorrectly requires fields for `write` or `commit`.
BRANCHES={
 "ui":[("submit","TurnsSubmitRequest","RunRecord"),("control","RunsControlRequest","Acknowledgement"),("review","ReviewsDecideRequest","ReviewSet")],
 "ingress":[("submit","TurnsSubmitRequest","RunRecord"),("events","EventsReadRequest","EventPage")],
 "agent.definitions":[("create","ToolAgentsCreateInput","DefinitionBatchResult"),("discover","ToolAgentsListInput","CandidatePage")],
 "agent.collaboration":[("delegate","DelegationSpec","AgentInstance"),("join","JoinRequest","AgentResult"),("handoff","ToolAgentsHandoffInput","ControlLease")],
 "agent.board":[("read","BoardReadRequest","BoardPage"),("commit","BoardCommitRequest","BoardEntry")],
 "agent.definitions.change_service":[("diff","DefinitionsDiffRequest","DefinitionDiff"),("update","DefinitionsUpdateRequest","AgentDefinitionVersion"),("revert","DefinitionsRevertRequest","AgentDefinitionVersion")],
 "context.ingestion":[("ingest","SourcesIngestRequest","IngestionRecord"),("delete","SourcesDeleteRequest","DeletionReceipt")],
 "context.memory":[("remember","MemoryCandidate","MemoryRecord"),("recall","ToolMemoryRecallInput","MemoryPage"),("forget","MemorySelector","DeletionReceipt")],
 "context.references":[("register","ReferenceRecord","ReferenceRecord"),("resolve","RefRequest","ResolvedReference"),("read","ReferencesReadRequest","ReadResult")],
 "tool.mcp":[("connect","McpConnectRequest","McpSession"),("discover","RefRequest","ToolPage"),("call","McpInvokeRequest","ProviderReceipt"),("close","RefRequest","Acknowledgement")],
 "workspace.binding":[("bind","ProjectsBindRequest","ProjectBinding"),("check_scope","ScopeCheckRequest","ValidationReport")],
 "workspace.isolation":[("allocate","WorkspaceSpec","WorkspaceRecord"),("release","RefRequest","Acknowledgement")],
 "workspace.environment":[("inspect","ToolEnvironmentInspectInput","EnvironmentRecord"),("ensure","ToolEnvironmentEnsureInput","EnvironmentRecord"),("release","RefRequest","Acknowledgement")],
 "workspace.process":[("read","ToolFileReadInput","FileContent"),("write","ToolFileWriteInput","ChangeSet"),("exec","ToolProcessExecInput","ProcessRecord"),("poll","ToolProcessPollInput","ProcessRecord"),("stop","ToolProcessStopInput","ProcessRecord")],
 "workspace.changes":[("changes","ToolWorkspaceChangesInput","ChangeSet"),("merge","WorkspacesMergeRequest","MergeResult"),("revert","WorkspacesRevertRequest","MergeResult")],
 "workspace.artifacts":[("register","ToolArtifactsPublishInput","ArtifactRecord"),("preview","ArtifactsPreviewRequest","DownloadTicket"),("export","ArtifactsExportRequest","DownloadTicket")],
 "workspace.review":[("get","ReviewsGetRequest","ReviewSet"),("decide","ReviewsDecideRequest","ReviewSet")],
 "run.history":[("append","InputRecord","InputRecord"),("read","ConversationsItemsRequest","ItemPage")],
 "run.events":[("append","EventAppendRequest","EventEnvelope"),("replay","EventsReadRequest","EventPage"),("subscribe","EventsStreamRequest","EventEnvelope")],
 "run.budget":[("reserve","BudgetReserveRequest","BudgetReservation"),("settle","BudgetSettleRequest","UsageSettlement"),("release","RefRequest","BudgetReservation")],
 "run.approval":[("request","ApprovalCreateRequest","ApprovalRequest"),("decide","ApprovalsDecideRequest","ApprovalGrant"),("control","RunControlRequest","Acknowledgement")],
 "run.resume":[("resume","RunsResumeRequest","RunRecord"),("replay","EventsReadRequest","EventPage")],
 "support.configuration":[("stage","AdminConfigurationStageRequest","ConfigurationVersion"),("activate","AdminConfigurationActivateRequest","ConfigurationVersion"),("connect","ConnectionsBeginRequest","AuthorizationStart"),("revoke","ConnectionsRevokeRequest","DeletionReceipt")],
 "support.extensions":[("install","AdminExtensionsInstallRequest","ExtensionManifest"),("activate","AdminExtensionsActivateRequest","ExtensionManifest"),("revoke","AdminExtensionsRevokeRequest","DeletionReceipt")],
 "support.cache":[("lookup","CacheLookupRequest","CacheLookupResult"),("put","CachePutRequest","CacheRecord"),("invalidate","CacheInvalidateRequest","Acknowledgement")],
 "support.observability":[("observe","TraceSpan","Acknowledgement"),("query","AdminTracesListRequest","TracePage")],
 "support.stores":[("get","StoreGetRequest","Ref"),("put","StorePutRequest","RepositoryReceipt"),("delete","StoreDeleteRequest","DeletionReceipt")],
 "context.memory.store":[("commit","MemoryCommitRequest","MemoryRecord"),("recall","ToolMemoryRecallInput","MemoryPage")],
 "tool.mcp.session":[("connect","McpConnectRequest","McpSession"),("health","RefRequest","McpSession"),("close","RefRequest","Acknowledgement")],
}
for name,owner,description,spec in [
 ("JoinRequest","agent","收集并核对依赖版本再归并。","required_result_refs|[](Ref)|子结果\nexpected_task_revision|Revision|任务版本\nreducer_spec|Ref|归并方法"),
 ("BoardReadRequest","agent","读当前获准共享板。","cursor?|Cursor|下一页\nlimit?|PageLimit|页大小"),
 ("BoardCommitRequest","agent","候选共享结果CAS。","entry_key|ID|条目\nresult_ref|Ref|结果\nexpected_board_revision|Revision|共享板版本\nprovenance|[](Ref)|来源\nstatus|BoardStatus|候选/确认"),
 ("McpConnectRequest","tool","批准绑定建立session。","provider_ref|Ref|绑定\nconnection_revision|Revision|连接版本\ntransport_config_ref|Ref|协议配置\ndeadline|Timestamp|截止"),
 ("McpInvokeRequest","tool","MCP不绕过Tool Runtime。","validated_call_ref|Ref|已过闸门调用\nsession_ref|Ref|session\nbusiness_key?|NonEmptyText|去重键\nattempt_id|ID|尝试"),
 ("ScopeCheckRequest","workspace","检查当前绑定仍有效。","binding_ref|Ref|绑定\nrequested_resource_refs|[](Ref)|访问目标\nrequested_capabilities|[](ID)|需要能力"),
 ("EventAppendRequest","run","持久日志分配seq，调用者不伪造seq。","stream_id|ID|流\nevent_id|ID|去重\nevent_type|NonEmptyText|已注册类型\npayload_ref|Ref|固定payload\nbase_revision?|Revision|预期原版本"),
 ("BudgetReserveRequest","run","原子预留账本。","reservation_id|ID|去重\nparent_run_id|ID|运行\nestimates|ResourceVector|额度\ndeadline|Timestamp|截止\nexpected_ledger_revision|Revision|CAS"),
 ("BudgetSettleRequest","run","使用已发生账单结算。","reservation_ref|Ref|预留\nusage|Usage|真实用量\nexpected_ledger_revision|Revision|CAS"),
 ("ApprovalCreateRequest","run","创建固定动作审批。","action_id|ID|动作\narguments_hash|Hash|参数\nresource_refs|[](Ref)|资源\neffect|EffectKind|效果\nsummary|NonEmptyText|可读行为\nexpires_at|Timestamp|截止"),
 ("CacheLookupRequest","support","可用缓存查找。","key|CacheKey|键\nnow|Timestamp|当前时间"),
 ("CachePutRequest","support","只缓存明确可复用结果。","record|CacheRecord|条目"),
 ("CacheInvalidateRequest","support","按依赖传播失效。","dependency_refs|[](Ref)|撤销/变更来源\nreason|NonEmptyText|原因"),
 ("StoreGetRequest","support","私有仓储读。","repository_kind|StoreKind|仓储\nkey|ID|键\nversion?|Version|固定版本"),
 ("StorePutRequest","support","私有仓储写不能变成任意数据库命令。","repository_kind|StoreKind|仓储\nkey|ID|键\ncontent_ref|Ref|schema校验后的对象\nexpected_version|Version|CAS\noperation_id|ID|去重"),
 ("StoreDeleteRequest","support","私有删除。","repository_kind|StoreKind|仓储\nkey|ID|键\nexpected_version|Version|CAS"),
 ("MemoryCommitRequest","context","仅提交经政策和冲突核验记忆。","validated_memory|MemoryRecord|候选\nexpected_revision|Revision|CAS\nnow|Timestamp|时间"),
 ]: record(name,owner,description,spec)
enum("StoreKind","history|object|index|cache|trace","support")

COMPONENT_REQUEST_OVERRIDES={
 "intent.preview":"IntentPreviewRequest", "agent.loop":"AgentStepRequest","agent.definitions.model_intent":"ModelPolicyRequest",
 "tool.invocation":"ToolCall", "workspace.base":"CaptureRequest", "model.policy":"ModelPolicyRequest","model.gateway":"ModelCall",
 "agent.collaboration.join":"JoinRequest", "run.cancel":"CancelInternalRequest", "run.checkpoint":"CheckpointCaptureRequest",
 "tool.invocation.schema":"NormalizeCallRequest", "tool.invocation.approval":"ApprovalCreateRequest",
}
record("CancelInternalRequest","run","取消树并保留成果。","target_run_ref|Ref|运行\ntarget_agent_refs?|[](Ref)|子树\nreason|NonEmptyText|原因\npreserve_artifact_refs|[](Ref)|保留")
record("CheckpointCaptureRequest","run","只从各域已提交仓储取得版本，pending游标可缺省。","committed_event_seq|Revision|事件提交点\ndomain_refs|DomainRefMap|跨域已提交版本\npending_call_cursor?|Cursor|未决工具位置\nschema_version|Version|格式")
scalar("DomainRefMap","run","域名到固定版本的映射。",type="object",additionalProperties=ref("Ref"),maxProperties=32,propertyNames={"pattern":"^[a-z][a-z0-9_.-]*$"})
record("NormalizeCallRequest","tool","只接受工具声明的参数，可信上下文另传。","tool_ref|Ref|完整固定工具版本\narguments|Object|参数\naction_id|ID|动作")

def type_expression(expression, name):
    expression=expression.strip()
    if expression.startswith(("list[","set[")):
        start=expression.index("[")+1
        result={"type":"array","items":type_expression(expression[start:-1],name),"maxItems":256}
        if expression.startswith("set["): result["uniqueItems"]=True
        return result
    if expression.startswith("dict["):
        _,value=expression[5:-1].split(",",1)
        return {"type":"object","additionalProperties":type_expression(value,name),"maxProperties":256,
                "propertyNames":{"pattern":"^[A-Za-z0-9][A-Za-z0-9._:-]*$"}}
    if "|" in expression: return {"type":"string","enum":expression.split("|")}
    builtin={"int":"Revision" if any(x in name for x in ["revision","version","epoch","seq"]) else "Count",
             "str":"Text","bool":"Bool"}
    return ref(builtin.get(expression,expression))

def tagged_union(name,branches,owner,output=False):
    variants=[]
    for action,request,response in branches:
        branch=name+"".join(x.capitalize() for x in action.split("_"))
        obj(branch,owner,"按action选择的独立参数/结果分支。",{
          "action":field({"type":"string","const":action},"分支标识"),
          "result" if output else "parameters":field(response if output else request,"该分支的明确结构")})
        variants.append(ref(branch))
    TYPES[name]={"description":"互斥分支；所有字段须匹配所选action。","oneOf":variants}
    OWNERS[name]=owner; RULES[name]=["禁止用一个动作的参数调用另一个动作；服务端先确定action再校验分支。"]

def register_private_components(graph, strategies):
    for node_id,strategy in strategies.items():
        node=graph["nodes"][node_id]; owner=node_id.split(".")[0]
        if owner in ["ui","ingress"]: owner="run"
        stem="Internal"+"".join(x.capitalize() for x in node_id.split("."))
        if node_id in BRANCHES:
            request=stem+"Request"; response=stem+"Output"
            tagged_union(request,BRANCHES[node_id],owner)
            tagged_union(response,BRANCHES[node_id],owner,True)
        elif node_id in COMPONENT_REQUEST_OVERRIDES:
            request=COMPONENT_REQUEST_OVERRIDES[node_id]; response=COMPONENT_OUTPUTS[node_id]
        else:
            request=stem+"Request"; fields={}
            for part in strategy["payload"].split(";"):
                key,expression=part.strip().split(":",1)
                expression=expression.strip(); optional=expression.endswith("?")
                if optional: expression=expression[:-1]
                fields[key]=field(type_expression(expression,key),PRIVATE_FIELD_NOTES.get(key,"见本接口输入约束与执行策略；类型定义限定结构。"),optional)
            obj(request,owner,node["label"]+"的私有阶段输入。",fields,[strategy["commit"],"服务端注入可信上下文，不通过HTTP或LLM工具直接访问。"])
            response=COMPONENT_OUTPUTS[node_id]
        effect="internal_write" if any(x in node["entry"] for x in ["commit","create","append","revert","register","write","release","transition","emit","publish","forget","invalidate","spawn"]) else "read"
        operation(node_id,"component",owner,node_id,request,response,effect,
          [strategy["commit"],*strategy["steps"],"取消/超时遵从COMMON_CONTRACTS；所有引用必须当前权限内、版本可访问。"],auth="service",errors=strategy["errors"])

PRIVATE_FIELD_NOTES={
 "original_input_ref":"获准且不可变的原始用户输入；不得指向模型摘要。",
 "source_input_ref":"真实用户输入来源，权限/模型覆盖必须可回溯。",
 "input_refs":"授权并固定实际版本的输入集合。",
 "evidence_refs":"实际取得、可读取且与本次要求有关的证据。",
 "expected_revision":"目标域CAS版本；不匹配返回conflict并重新读取。",
 "expected_versions":"每个参与资源的预期修订，不允许缺失应校验的资源。",
 "deadline":"绝对UTC截止；重试和子调用不能延长父deadline。",
 "max_calls":"只读探查调用上限，必须在预留预算内。",
 "attempt_id":"实际执行尝试；每次重试不同，与稳定action_id分开。",
 "action_id":"逻辑动作稳定去重键；超时后恢复必须沿用。",
 "remaining_budget":"父账本核准剩余额度，仅是快照，调度前仍预留。",
 "failure":"真实失败原因；不可仅凭retryable跳过未知效果核验。",
 "expected_resource_revision":"调用目标当前版本必须匹配；审批后再次检查。",
 "capability_snapshot":"当前有效能力及旗标版本，用于缩小候选。",
 "candidate_refs":"权限过滤后的候选块，未读取内容不能直接当证据。",
 "target_tokens":"压缩输出预算；不可通过丢弃必需要求满足。",
 "model_context_limit":"实际选定模型窗口，含输入及输出和工具保留。",
 "output_reserve":"保留生成Token，不能被输入填满。",
 "tool_reserve":"保留工具往返Token。",
 "context_epoch":"上下文纪元，旧快照不能向新纪元追加。",
 "parent_agent_ref":"父实例必须同一任务树且仍拥有有效权限/预算。",
 "creation_key":"重复创建同一输入返回已有实例；不同输入相同键冲突。",
 "pending_call_refs":"已发出但未确定效果的调用；先对账再重放。",
 "expected_artifact_versions":"待完成成果的实际版本；内容变化使旧验证失效。",
 "provider_ref":"管理员配置且当前可用的固定提供方版本。",
 "normalized_arguments_hash":"规范参数摘要，用于审批/幂等与复核。",
 "provenance":"所有结果来源及派生路径，不允许伪造引用。",
 "now":"服务端可信时间，不接受客户端时间改变有效期。",
 "retention":"记忆保留毫秒数，最终由有效政策限定。",
 "lease_ttl":"毫秒；必须>0，不得超过Run deadline。",
 "expected_environment_ref":"恢复时要求的实际环境版本；不匹配需重新准备和核验。",
}

PRIVATE_FIELD_NOTES.update({
 "account_connection_ref":"用户批准的外部账号连接，须仍active且范围符合。",
 "activated_skill_refs":"本轮已激活的固定技能版本，按作用域继承方法。",
 "active_revisions":"每个语料当前已发布的索引修订；旧未发布索引不得混入。",
 "actor":"由可信认证产生的操作主体，不能由模型正文自报。",
 "actual_config_ref":"本次真实使用的模型配置，不能只记录用户希望的配置。",
 "affected_revision":"发生撤销/能力变化的绑定修订，用于失效传播。",
 "agent_tree_ref":"当前运行的实例树版本，限定取消传播范围。",
 "allowed_scope":"有效权限交集内的允许范围，不能由发现结果扩大。",
 "approval_ref":"参数和资源版本匹配、未过期的授权依据。",
 "artifact_manifest_ref":"本次交付成果的不可变清单。",
 "artifact_refs":"实际存在、获准且固定版本的成果；不接受虚构路径。",
 "attempt_usage":"这次真实尝试的已知用量；未知账单标记pending。",
 "attempts":"已执行尝试总数，包括首次与失败；用于重试上限。",
 "available_resources":"当前可用资源快照；实际调度仍原子预留。",
 "baseline_manifest":"同任务预算基线的系统版本清单。",
 "batch_policy":"atomic整批提交或independent逐项提交。",
 "budget":"任务/分工资源上限，不能超过父预留。",
 "budget_estimate":"派发前估算的资源，失败尝试也进入结算。",
 "business_key":"提供方认可的逻辑幂等键；重试沿用。",
 "call_ref":"实际调用记录及固定参数版本。",
 "cancel_reason":"取消理由；账本仍保留已发生费用和外部效果。",
 "candidate_kind":"explicit来源于用户明确要求；inferred先候选后核验。",
 "candidate_manifest":"待测候选系统/方法/适配器版本清单。",
 "candidate_ref":"尚未确认的记忆/结果候选版本。",
 "candidate_scope":"指代消解允许搜索的资源范围。",
 "checkpoint_ref":"已提交检查点，不能是模型虚构摘要。",
 "completion_proposal_ref":"Completion Controller的当前成果完成提案。",
 "constraints":"有用户/政策来源的任务硬约束。",
 "content":"有来源且受当前记忆政策约束的内容。",
 "contract_ref":"当前目标和验收要求的固定版本。",
 "conversation_id":"当前获准会话，服务校验与可信上下文一致。",
 "corpus_refs":"授权并发布的检索语料；删除资料不可用旧缓存召回。",
 "coverage_gaps":"缺乏证据的验收要求ID，用于申请实际检查。",
 "current_config_revision":"恢复时有效配置版本，含当前撤销与能力开关。",
 "current_principal":"恢复请求的当前认证主体，不继承旧过期权限。",
 "current_runtime_manifest":"正在运行代码与协议的实际版本清单。",
 "dataset_version":"固定任务样本版本，候选与基线须一致。",
 "decision":"真实用户审阅决定；与模型语义核验区分。",
 "decision_question":"需要本次复评的具体问题，避免重做全部理解。",
 "definition_ref":"可用且绑定当前会话的固定角色定义版本。",
 "definitions_revision":"候选角色目录修订，用于缓存及失效。",
 "delegation_ref":"目标、资料、验收与预算已经固定的委派契约。",
 "deletion_id":"稳定删除事务ID，重复请求不重复删除。",
 "delivery_contract_ref":"用户原文/修订形成的当前交付标准。",
 "derived_dependency_refs":"待删除资源派生的索引/摘要/缓存，须传播失效。",
 "design_method_ref":"主Agent按需加载的精炼角色设计方法。",
 "domain_resource_refs":"检查点固定的各业务域资源，恢复逐个复核。",
 "draft":"待校验草案，不是已授权可运行实例。",
 "effect_state":"外部效果confirmed/pending/unknown，不能凭HTTP200推断。",
 "effective_policy_ref":"当前有效权限/旗标/审批政策版本。",
 "effective_scope":"父、角色、产品、设备权限求交后的真实范围。",
 "equivalence_contract_ref":"能力、信息范围与效果已登记等价的替代契约。",
 "existing_agent_refs":"当前可用实例/角色摘要，避免无必要新增Agent。",
 "existing_definition_refs":"当前会话已保存定义，避免重复职责或同名。",
 "existing_names":"已占用角色名称，按规范化唯一规则比对。",
 "existing_refs":"同作用域的已有记忆版本，用于语义冲突核对。",
 "expected_artifact_version":"用户审阅时所见成果版本，变化需重新审阅。",
 "expected_config_revision":"连接/提供方预期配置修订；变化重新读取。",
 "expected_control_revision":"控制租约域CAS版本，防止双控制者。",
 "expected_registry_revision":"工具目录CAS修订，发布后再更新派生索引。",
 "expected_revisions":"所有参与完成提交的资源预期修订。",
 "expected_run_revision":"Run状态CAS修订，过期执行者不能推进新状态。",
 "expressions":"用户原文中待消解的指代/文件/材料称呼。",
 "feedback_ref":"用户针对当前成果的实际反馈。",
 "fixture_environment":"固定评测环境、输入初态与允许副作用。",
 "freshness":"固定版本、最新必需或政策限定时效。",
 "from_agent_ref":"移交前当前控制实例，必须持有有效租约。",
 "from_ref":"同任务树内真实发送者，由认证上下文核验。",
 "goal":"当前目标，必须保留原文与已确认修订的含义。",
 "grader_config":"固定评分方法与人工/语义评审政策。",
 "impact":"理解错误可能产生的影响，用于决定澄清或可逆探查。",
 "instruction_set_ref":"按来源优先级和作用域解决的指令集合。",
 "interpretations":"有用户原文来源的理解候选，不是虚构新目标。",
 "item_patch":"按base_revision应用的交互项增量/替换。",
 "material_refs":"任务指定或相关的获准实际材料版本。",
 "max_candidates":"一次最多提供候选数，减少模型输入而不授予权限。",
 "memory_policy_ref":"当前记忆读取/贡献/范围/保留政策。",
 "message_id":"协作消息去重键，重复同内容返回原消息。",
 "messages":"按顺序发送给提供方的有来源消息块。",
 "migration_policy":"检查点跨协议版本迁移的批准策略。",
 "missing_facts":"影响任务执行但尚未知道的具体事实。",
 "node_id":"任务图中的具体节点；租约范围可为整个Run。",
 "node_states":"当前计划版本每个节点的执行状态。",
 "occurrence_key":"定时/事件这一次触发的稳定去重键。",
 "output_contract":"本分工的目标、必须成果和真实证据标准。",
 "output_specs":"预期交付类型、用途和是否必需。",
 "overlap_policy":"已有运行未结束时排队、跳过或获准并行。",
 "parent_goal_ref":"父当前理解/要求版本，防止子目标偏离。",
 "payload_refs":"允许共享的固定资料/候选结果，不传整个私有上下文。",
 "pending_action_refs":"未确认效果动作，恢复前需查回执。",
 "pending_effect_refs":"完成提交时尚未知的外部效果，阻止虚假成功。",
 "plan_ref":"已校验、已提交的计划修订，不是未接受建议。",
 "previous_attempt_ref":"上一次真实模型尝试，流式已有输出时避免重复呈现。",
 "proposal_ref":"已经核对版本/证据的完成提案。",
 "proposed_goal":"父Agent拟定的有界子目标，待委派契约核对。",
 "proposed_outcome":"建议结果；代码完成闸门验证后才提交终态。",
 "proposed_requirements":"模型提取的候选要求，核对用户原文与政策来源。",
 "provider_binding_ref":"有效提供方配置与账号授权的固定绑定。",
 "provider_kind":"内部、本地、MCP或API适配通道。",
 "provider_result_ref":"真实提供方响应原始记录，不含回显秘密。",
 "provider_usage":"提供方报告的实际账单；无数据则pending而非0。",
 "purpose":"此次上下文用途，选择相关构建/压缩/裁剪功能。",
 "query":"按当前语义任务生成的检索查询，不使用行业词典固定路由。",
 "reason":"明确操作理由；不得用理由文字替代权限/版本校验。",
 "reasoning_config":"仅提供方已登记支持的推理配置，不能覆盖用户模型。",
 "reconciled_state_refs":"恢复后已经复核/对账的业务域版本。",
 "registry_revision":"本次发现消费的工具目录修订。",
 "report_ref":"绑定当前成果版本的真实核验报告。",
 "reservation_ref":"父账本内已预留资源，派发前必须有效。",
 "reserved_budget_ref":"本次模型调用对应预算预留。",
 "resolved_model_id":"在用户固定政策或Auto授权内解析的实际目录ID。",
 "resumable_nodes":"通过依赖/权限/环境/效果核验的可续跑节点。",
 "retry_policy_ref":"次数、退避、截止、等价切换限制的固定版本。",
 "reversible":"错误动作是否有已知可逆策略；不能等同无风险。",
 "review_set_ref":"固定成果/变更版本的用户审阅集合。",
 "reviewer_policy":"语义评审方法、模型继承和预算，不替代真实检查。",
 "role_capabilities":"角色允许的类别，发现时与有效权限求交。",
 "role_constraints":"任务所需职责与不能进行的动作。",
 "role_profile_ref":"平台角色固定版本，与用户定义不能任意扩权限。",
 "run_id":"当前Run，主体及会话关联由服务核验。",
 "scope_paths":"获准项目路径引用，用于查找作用域项目规则。",
 "selected_block_refs":"经过预算分配、来源/权限核对的上下文块。",
 "selector":"明确范围的记忆选择，不是任意数据库查询。",
 "session_ref":"当前active的MCP连接session及能力修订。",
 "slot_key":"同主题互斥事实/偏好的逻辑位置。",
 "source_refs":"实际来源集合，须固定版本、访问权和可定位内容。",
 "source_revision_policy":"允许固定旧版本或要求最新；变化时反馈stale。",
 "spec":"已按固定schema声明的完整工具契约。",
 "stable_item_keys":"与每个草案位置一一对应的稳定去重键。",
 "target_scope":"候选记忆/资源生效范围，只能在当前权限内缩小。",
 "target_task_ref":"定时触发所绑定任务版本。",
 "task_frame_ref":"当前任务理解，包含原文和明确约束来源。",
 "task_goal":"当前目标摘要，仅用于候选排序，不覆盖原文。",
 "task_revision":"协作消息或结果依赖的共同任务修订。",
 "to_agent_ref":"同任务树且有匹配角色/权限的目标实例。",
 "to_ref":"同任务树获准接收实例，不能越界投递资料。",
 "tool_id":"工具稳定名，固定version后才可以执行。",
 "tool_ledger_cursor":"检查点处的效果账本位置，用于续接对账。",
 "tools":"本次实际暴露给模型的工具参数schema，按稳定版本排序。",
 "top_k":"检索最多命中数，1–64；过滤访问权后再排序。",
 "transition":"明确from/to状态与真实依据，须满足状态白名单。",
 "trigger_spec_ref":"获准触发规则、目标、范围和重叠策略版本。",
 "unfinished_refs":"移交给新控制者的未完工作与待定状态引用。",
 "unresolved":"当前还没有答案的关键问题，不自动当成已解决。",
 "usage":"全部真实attempt消耗，账单不确定性显式记录。",
 "user_input_ref":"当前用户明确要求的原始输入，不是模型推断授权。",
 "user_input_refs":"原始用户输入及有效补充，解析交付要求的依据。",
 "user_instruction_refs":"用户当前要求和获准偏好规则，保留来源。",
 "user_patch_refs":"运行中追加的用户要求版本，原文不覆盖。",
 "user_source_ref":"授权/创建/模型覆盖来源，必须是真实用户行为。",
 "validated_action_ref":"已经schema/precheck/recheck的固定动作。",
 "validated_call":"已经经过闸门且参数Hash固定的工具调用。",
 "validated_call_ref":"已规范化、已授权调用记录及版本。",
 "validated_drafts":"经过定义、依赖、权限和模型意图核对的草案。",
 "verification_refs":"与成果实际版本匹配的命令/结构/引用/语义证据。",
 "version":"不可变工具/方法/对象版本，不作为单调整数比较。",
 "visible_capabilities":"当前已过滤角色/旗标/主体权限的能力摘要。",
 "workspace_ref":"获准工作区和实际文件树版本。",
})

def finalize(graph,strategies):
    obj("BackgroundRunJob", "run", "内部有界持久单Agent任务；claim栅栏不替代执行权限，恢复原attempt。", {
        "run_id": field("ID", "原Run"), "principal": field("Principal", "原认证用户会话"),
        "revision": field("Revision", "持久CAS"), "fence": field("Revision", "单调worker栅栏"),
        "state": field({"type":"string", "enum":["queued","working","waiting","blocked","finished"]}, "调度状态"),
        "stage": field({"type":"string", "enum":["admitted","prepared","understood","started","step","delivery","finished"]}, "原执行阶段"),
        "step": field({"type":"integer", "minimum":0, "maximum":64}, "原步骤序号"),
        "ready_at": field("Timestamp", "下次检查时间"),
        "worker_id": field("ID", "当前进程holder", True), "lease_expires": field("Timestamp", "holder期限", True),
        "context": field("TrustedExecutionContext", "实际Run/模型/政策绑定", True),
        "frame_ref": field("Ref", "实际理解版本", True), "role_ref": field("Ref", "实际根角色", True),
        "instance_ref": field("Ref", "原根实例", True),
        "step_context": field("TrustedExecutionContext", "原步骤attempt/operation，不以新调用替代", True),
        "proposal_ref": field("Ref", "实际完成提案", True),
        "failure": field("Failure", "保留失败或未知效果", True),
    })
    scalar("ArtifactPreviewText", "workspace", "完整UTF-8文本预览；服务再检查最大65536字节和SHA256，不截断。", type="string", maxLength=65536)
    obj("ArtifactContentView", "workspace", "实际文本或Markdown成果正文。", {
        "artifact": field("ArtifactRecord", "不可变成果元数据"),
        "content": field("ArtifactPreviewText", "完整正文"),
    })
    obj("RunDeliveryView", "run", "真实成果、合同、逐项核验、完成提案的固定视图；不返回执行上下文。", {
        "run_id": field("ID", "所属Run"), "bundle_ref": field("Ref", "固定Bundle"),
        "artifact_ref": field("Ref", "固定成果"), "artifact": field("ArtifactRecord", "成果记录"),
        "content": field("ArtifactPreviewText", "实际正文"),
        "contract_ref": field("Ref", "固定合同"), "contract": field("Contract", "原要求合同"),
        "report_ref": field("Ref", "固定报告"), "report": field("VerificationReport", "逐项报告"),
        "proposal_ref": field("Ref", "固定提案"), "proposal": field("DeliveryProposal", "候选提案"),
        "requires_acceptance": field("Bool", "合同要求用户接受"), "stale": field("Bool", "相对于当前任务版本过时"),
        "acceptance": field("CompletionAcceptance", "实际用户决定", True),
    })
    endpoint("runs.delivery", "GET", "/v1/runs/{run_id}/delivery", "run", "ui run.history workspace.artifacts", "读取本人Run的最新真实固定交付；无交付返回missing。", "run_id|ID|运行", "RunDeliveryView")
    endpoint("artifacts.content", "GET", "/v1/artifacts/{artifact_id}/content", "workspace", "ui workspace.artifacts", "读取完整文本/Markdown；固定版本与hash必需。", "artifact_id|ID|成果\nversion|Version|精确版本\ncontent_hash|Hash|预期SHA256", "ArtifactContentView")
    endpoint("runs.delivery.accept", "POST", "/v1/runs/{run_id}/delivery/acceptance", "run", "ui run.state workspace.artifacts", "实际用户决定整份合同交付；不直接设置completed。", "run_id|ID|运行\nbundle_ref|Ref|精确Bundle\nartifact_ref|Ref|精确成果\ndecision|DeliveryDecision|accept或reject", "CompletionAcceptance", "internal_write", ["当前认证身份必须与原执行用户会话一致；只接受要求用户接受的合同；版本/取消复核。"])
    TYPES["RunsDeliveryAcceptRequest"]["properties"]["decision"] = {"type":"string", "enum":["accept","reject"], "description":"现有DeliveryDecision的整份接受/拒绝子集。"}
    obj("ConversationListVersion", "run", "同用户会话列表固定版本，不是授权凭据。", {
        "id": field("ID", "会话"), "revision": field("Revision", "读取时固定版本"),
    })
    obj("ConversationListSnapshot", "run", "内部持久分页快照；一小时失效，最多4096会话，超容量明确不可用。", {
        "id": field("ID", "分页身份"),
        "expires": field({"type":"integer", "minimum":0}, "Unix秒期限"),
        "versions": field(arr("ConversationListVersion",4096), "创建顺序的固定版本"),
    })
    endpoint("turns.lookup", "GET", "/v1/conversations/{conversation_id}/turn-requests/{request_id}", "run", "ui ingress run.history", "按原提交request_id查询当前Run；没有记录返回missing，不发送新任务。", "conversation_id|ID|原会话\nrequest_id|ID|原RequestMeta.request_id", "RunRecord", rules=["仅认证拥有者；不返回其他动作的请求回执；当前Run变化不改变原提交身份。"])
    obj("WebLaunch", "run", "CLI用户取得短期一次Web启动链接；fragment凭据不能进入日志或持久缓存。", {
        "launch_url": field("URL", "精确localhost Web origin与一次code fragment"),
        "expires_at": field("Timestamp", "两分钟内截止"),
    })
    obj("WebSession", "run", "浏览器用户身份和CSRF；会话凭据只在HttpOnly cookie中。", {
        "principal": field("Principal", "服务器签发的用户和Web session"),
        "expires_at": field("Timestamp", "固定会话截止"),
        "csrf_token": field("Hash", "内存保留，修改请求X-UAW-CSRF"),
    })
    for name, states in (("WebLaunchTicket", ["issued", "consumed"]), ("WebSessionRecord", ["active", "revoked"])):
        obj(name, "run", "内部持久身份记录，不含原bearer、启动code、cookie或CSRF。", {
            "id": field("ID", "随机记录身份"), "principal": field("Principal", "独立认证用户"),
            "origin": field("URL", "精确Web origin"), "credential_epoch": field("Hash", "当前账号凭据纪元"),
            "expires_at": field("Timestamp", "有界期限"), "state": field({"type":"string", "enum": states}, "当前状态"),
            "revision": field("Revision", "持久CAS版本"),
        })
    endpoint("web.launch", "POST", "/v1/web/launch", "run", "ui ingress run.history", "CLI用户取得启动链接。", "", "WebLaunch", "internal_write", ["无Origin的用户Bearer；管理员拒绝；两分钟一次凭据。"])
    endpoint("web.session.exchange", "POST", "/v1/web/session", "run", "ui ingress run.history", "精确Origin消费一次启动code。", "launch_code|NonEmptyText|原启动fragment凭据", "WebSession", "internal_write", ["无Bearer/旧cookie；串行一次消费，任何重放拒绝；HttpOnly SameSite Strict host-only cookie。"], auth="public")
    TYPES["WebSessionExchangeRequest"]["properties"]["launch_code"].update(maxLength=256)
    endpoint("web.session.get", "GET", "/v1/web/session", "run", "ui ingress run.history", "读取当前浏览器用户会话。", "", "WebSession")
    endpoint("web.session.logout", "DELETE", "/v1/web/session", "run", "ui ingress run.history", "撤销当前浏览器会话并清cookie。", "", "Acknowledgement", "internal_write", ["{meta,payload}正文；精确Origin/HttpOnly cookie/X-UAW-CSRF；无If-Match参数。"])
    enum("RunnerBindingState","active|revoked|expired","run")
    enum("RunnerCommandState","active|revoked","run")
    record("RunnerChannelSnapshot","run","独立可信通道源读取的当前设备拥有者及认证身份，不接受网络/模型自报。","device_id|ID|设备\nowner|Principal|原用户\nactor|Principal|当前认证Runner\npairing_ref|Ref|实际配对版本\nchannel_ref|Ref|实际通道版本\nkey_ref|Ref|设备公钥版本\nconnected|Bool|实际在线\nexpires_at|Timestamp|当前通道期限")
    record("RunnerDeviceBinding","run","平台拥有的设备/通道归属，撤销与到期不自动复活。","device_id|ID|设备\nrevision|Revision|CAS\nsource|RunnerChannelSnapshot|登记时实际来源\nstate|RunnerBindingState|当前状态")
    record("RunnerDeviceBindRequest","run","内部认证控制服务登记当前真实通道，不接受owner声明。","device_id|ID|设备\nchannel_ref|Ref|独立来源\nexpected_revision|Revision|当前CAS")
    record("RunnerRequestRegisterRequest","run","内部控制服务登记不可变实际业务参数。","id|ID|稳定请求\nparameters|RunnerParameters|实际业务参数")
    record("RunnerRequestRecord","run","版本1的原请求/原尝试，不是执行权限。","id|ID|稳定请求\ncontext|TrustedExecutionContext|服务取得的原上下文\nparameters|RunnerParameters|原业务参数")
    record("RunnerToolRequestRecord","run","控制服务登记的原 Tool 调用；不修改原上下文或授予发送权限。","id|ID|原Tool动作身份\ncontext|TrustedExecutionContext|完整原Tool上下文\nparameters|RunnerParameters|原文件读取参数\ncall|ValidatedCall|独立Tool账本的原规范化调用\nspec|ToolSpec|独立Tool账本的原工具版本")
    record("RunnerRootSnapshot","run","真实授权根来源的当前opaque元数据，不包含本机路径。","owner|Principal|原用户\ndevice_id|ID|设备\nworkspace_ref|Ref|实际工作区\nroot_handle|ID|授权根\nbinding_revision|Revision|根版本\nallowed_actions|[](ID)|当前获准读动作\nexpires_at|Timestamp|根期限")
    record("RunnerCommandDraft","run","控制服务从独立登记源构建的签字正文。","command_id|ID|命令\noperation_id|ID|原操作\nrequest_ref|Ref|原请求\ntrusted_context|TrustedExecutionContext|原上下文\nfencing_token|Revision|当前栅栏\nexpires_at|Timestamp|有界期限\nparameters|RunnerParameters|原业务参数")
    record("RunnerCommandRegisterRequest","run","仅内部控制服务可创建签字记录，不发送命令。","command_id|ID|稳定命令\nrequest_ref|Ref|已登记实际请求\ndevice_ref|Ref|当前设备绑定\nlease_ref|Ref|当前根租约\nfencing_token|Revision|栅栏\nexpires_at|Timestamp|期限")
    record("RunnerCommandRecord","run","已签名不可变命令及登记来源；状态撤销不覆盖签字正文。","command|RunnerCommand|实际签字正文\ndevice_ref|Ref|固定设备绑定\nlease_ref|Ref|固定租约\nholder|Principal|真实执行服务\nroot|RunnerRootSnapshot|实际根来源\nrevision|Revision|登记状态CAS\nstate|RunnerCommandState|是否允许新准入")
    record("BudgetAttemptState","run","预算owning-domain当前实际意图/期限，查询不授权发送。","run_id|ID|运行\noperation_id|ID|原操作\ntrace_id|ID|原trace\nattempt_id|ID|原尝试\nreservation_ref|Ref|当前预留版本\ndeadline|Timestamp|实际尝试期限\ndispatched|Bool|已保存预算dispatch意图")
    record("BudgetExecutionSnapshot","run","单次MVCC读取的预算执行状态，保留未知费用语义。","ledger|RootBudgetLedger|当前根预算\nreservation|BudgetReservation|原尝试预留\nattempt|BudgetAttemptState|原尝试状态")
    scalar("ExecutionLeaseTtl","run","有界租约TTL毫秒，不超过Run截止时间。",type="integer",minimum=1,maximum=300000)
    enum("ExecutionLeaseState","active|released|expired|revoked","run")
    record("ExecutionLeaseStateRecord","run","同Run根执行租约的当前持久状态，终态不因时钟回退复活。","lease|ExecutionLease|当前租约\nstate|ExecutionLeaseState|状态",["行revision等于lease.revision；新接管递增fencing_token，续约不改变fence；不授予工具/文件/设备权限。"])
    record("ExecutionLeaseAcquireRequest","run","内部可信执行服务申请根租约。","lease_ttl_ms|ExecutionLeaseTtl|有界期限\nexpected_revision|Revision|当前状态CAS，初次为0")
    record("ExecutionLeaseRenewRequest","run","同一真实holder续约，不延长Run上限。","lease_ref|Ref|当前固定租约\nfencing_token|Revision|当前栅栏\nlease_ttl_ms|ExecutionLeaseTtl|新期限")
    record("ExecutionLeaseReleaseRequest","run","同一holder释放原租约，可在Run取消后清理。","lease_ref|Ref|当前固定租约\nfencing_token|Revision|当前栅栏")
    enum("ReconciliationOutcome","applied|not_applied|unknown","tool")
    record("ToolReconciliationReceipt","tool","可信提供方的固定动作核对回执，不能由模型或超时推测构造。","action_ref|Ref|固定动作\nattempt_id|ID|实际尝试\nprovider_ref|Ref|固定提供方\nreceipt_ref|Ref|当前读取回执\noutcome|ReconciliationOutcome|效果结论\nevidence_refs|[](Ref)|可重新读取的证明\nusage|Usage|实际或待核对消耗\nobserved_at|Timestamp|观察时间",["Reader校验真实来源、主体、签名/完整性和固定版本；调用方比较action/attempt/provider/receipt，并核对usage.attempt_id。", "applied/not_applied必须有证据；not_applied不代表零用量或允许重发；unknown保留额度，不从超时或未记dispatch推导未执行。"])
    TYPES["ToolReconciliationReceipt"]["allOf"]=[{"if":{"properties":{"outcome":{"enum":["applied","not_applied"]}},"required":["outcome"]},"then":{"properties":{"evidence_refs":{"minItems":1}}}}]
    record("RunnerAuthoritySnapshot","workspace","可信异步通道及服务记录解析的当前执行权威；没有本机路径或自报批准字段。","context|TrustedExecutionContext|实际授权上下文\ndevice_id|ID|当前设备\nroot_handle|ID|实际授权根\nworkspace_ref|Ref|工作区版本\nbinding_revision|Revision|根绑定版本\nfencing_token|Revision|当前栅栏\nlease_expires_at|Timestamp|当前租约期限\nrequest_ref|Ref|存储业务请求\nrequest_parameters|RunnerParameters|存储业务参数\npolicy_ref|Ref|当前政策\nrequired_scope_capability|NonEmptyText|需要的能力\nallowed_actions|[](ID)|当前获准动作\nfeature_enabled|Bool|实际开关\nconnected|Bool|实际连接\ncancelled|Bool|当前取消状态",["来源必须是认证通道和拥有者存储，command.trusted_context仅供对比，不能作为权威来源。", "snapshot不允许缓存后执行；所有字段必需，无默认批准/无限期限；没有真实authority或IPC时不可用。"])
    TYPES["UserInputRef"]={"description":"真实用户输入或已认证用户配置动作的引用；结构限制为input，来源真实性仍由Run核验。","allOf":[ref("Ref"),{"properties":{"kind":{"const":"input"}}}]}
    OWNERS["UserInputRef"]="common";RULES["UserInputRef"]=["必须解析到同主体真实用户行为记录；不能引用网页/模型输出授权创建、模型覆盖或审批。"]
    record("AuthenticationFailure","common","认证失败不透露受保护资源存在性。","code|ID|稳定认证错误码\nmessage|Text|安全提示\nrequest_id|ID|关联")
    TYPES["AuthenticationFailure"]["properties"]["code"]["const"]="authentication_required"
    TYPES["Failure"]["properties"]["message"]=dict(ref("NonEmptyText"),description="面向用户的明确失败原因；不得为空。")
    TYPES["RequirementVerdict"]["allOf"]=[{"if":{"properties":{"state":{"const":"passed"}},"required":["state"]},"then":{"properties":{"evidence_refs":{"minItems":1}}}}]
    TYPES["VerificationCheck"]["allOf"]=[{"if":{"properties":{"state":{"const":"passed"}},"required":["state"]},"then":{"properties":{"evidence_refs":{"minItems":1}}}},{"if":{"properties":{"kind":{"const":"command"},"state":{"enum":["passed","failed"]}},"required":["kind","state"]},"then":{"required":["process_ref"]}}]
    TYPES["DeliveryProposal"]["allOf"]=[{"if":{"properties":{"outcome":{"const":"succeeded"}},"required":["outcome"]},"then":{"properties":{"unresolved_effect_refs":{"maxItems":0}}}}]
    TYPES["ToolResult"]["allOf"]=[{"if":{"properties":{"status":{"const":"failed"}},"required":["status"]},"then":{"required":["failure"]}},{"if":{"properties":{"status":{"const":"succeeded"}},"required":["status"]},"then":{"properties":{"effect_state":{"const":"confirmed"}}}}]
    enum("IngestionState","pending|parsing|indexing|validating|published|failed|deleted|cancelled","context")
    TYPES["IngestionRecord"]["properties"]["status"]=dict(ref("IngestionState"),description="摄取作业状态；published才成为可检索active版本。")
    TYPES["RoleProfile"]["properties"]["model_capability_requirements"]=dict(ref("CapabilityRequirements"),description="可选角色能力要求，固定模型不满足时反馈，不能暗换。")
    TYPES["RoleProfile"]["properties"]["auto_model_candidates"]=dict(arr("ID",64),description="仅Auto已授权时进一步收窄候选，explicit/inherit不使用此列表替换模型。")
    TYPES["RequestMeta"]["properties"]["schema_version"]["const"]="0.1"
    if "task_frame" not in TYPES["RefKind"]["enum"]:TYPES["RefKind"]["enum"].append("task_frame")
    TYPES["RefKind"]["enum"]+= [x for x in "conversation run source rule role_profile template corpus chunk check board provider connection extension blob item event upload reservation budget lease approval trigger device project".split() if x not in TYPES["RefKind"]["enum"]]
    TYPES["MemorySelector"]["properties"]["ids"]["minItems"]=1
    TYPES["ProviderDraft"]["required"].remove("endpoint")
    TYPES["ProviderDraft"]["allOf"]=[{"if":{"properties":{"kind":{"enum":["api","model"]}},"required":["kind"]},"then":{"required":["endpoint"]}},{"if":{"properties":{"kind":{"enum":["runtime","local"]}},"required":["kind"]},"then":{"not":{"required":["endpoint"]}}}]
    RULES["ProviderDraft"].append("api/model需要网络地址；runtime/local不接受网络地址；MCP HTTP或stdio的配置按固定profile独立校验，stdio执行不能把Runtime服务当任务沙箱。")
    # Multi-action planner/memory/MCP components are explicitly tagged, not ad-hoc DTOs.
    BRANCHES["agent.planning"]=[("plan","ToolTasksPlanInput","TaskGraph"),("validate","GraphValidateRequest","ValidationReport")]
    BRANCHES["agent.skills"]=[("discover","SkillDiscoveryRequest","SkillPage"),("load","ToolSkillsLoadInput","SkillSpec")]
    BRANCHES["model.catalog"]=[("list","ToolModelsListInput","ModelPage"),("resolve","ModelResolveRequest","ModelCatalogEntry")]
    BRANCHES["model.capability"]=[("check","ModelCapabilityRequest","CapabilityCheck"),("select","ModelCapabilityRequest","CapabilityCheck")]
    BRANCHES["tool.results"]=[("normalize","NormalizeResultRequest","ToolResult"),("page","ToolResultPageRequest","ToolResult")]
    BRANCHES["tool.effects"]=[("record_intent","EffectIntentRequest","EffectRecord"),("reconcile","ReconcileRequest","EffectRecord")]
    BRANCHES["context.compression"]=[("compress","CompressionRequest","CompressionResult"),("validate","CompressionValidateRequest","ValidationReport")]
    BRANCHES["tool.mcp.capabilities"]=[("discover","RefRequest","ToolPage"),("register","RemoteCapabilityRequest","ToolPage")]
    BRANCHES["context.selection"]=[("select","SelectionRequest","SelectionResult"),("allocate","SelectionRequest","SelectionResult")]
    BRANCHES["support.extensions"] += [("validate","AdminExtensionsValidateRequest","ValidationReport"),("rollback","AdminExtensionsRollbackRequest","ExtensionManifest")]
    BRANCHES["context.ingestion"].append(("publish","IngestionPublishRequest","IngestionRecord"))
    BRANCHES["support.cache"].append(("get_or_compute","CacheComputeRequest","CacheLookupResult"))
    BRANCHES["agent.completion"]=[("verify","ToolTasksVerifyInput","VerificationReport"),("propose_completion","CompletionProposalRequest","DeliveryProposal")]
    COMPONENT_OUTPUTS["run.resume.lease"]="ExecutionLease"
    for name,owner,description,spec in [
      ("GraphValidateRequest","agent","校验结构、依赖和计划边界，不提交执行。","graph|TaskGraph|待检验图\ncurrent_frame_ref|Ref|当前目标"),
      ("SkillDiscoveryRequest","agent","按任务发现技能摘要。","query|NonEmptyText|目标\nrole_ref?|Ref|角色\nmax_candidates|CandidateLimit|数量"),
      ("ModelResolveRequest","model","把用户指定名称解析为可用目录ID。","requested_name|NonEmptyText|用户指定\nsource_input_ref|Ref|来源\nrequired_capabilities|[](ID)|要求"),
      ("ModelCapabilityRequest","model","当前模型能力核对与Auto候选选择共用明确请求。","policy_ref|Ref|授权政策\nrequirements|CapabilityRequirements|能力\ncontext_tokens|Count|输入\nbudget_ref|Ref|预留"),
      ("NormalizeResultRequest","tool","规范真实提供方结果。","raw_result_ref|Ref|原始回执\nprovider_status|NonEmptyText|传输状态\nbusiness_status?|NonEmptyText|业务状态\neffect_state|EffectState|效果\noutput_schema_ref|Ref|业务schema"),
      ("ToolResultPageRequest","tool","已登记工具结果分页。","result_ref|Ref|结果\ncursor?|Cursor|位置\nlimit|PageLimit|数量"),
      ("EffectIntentRequest","tool","派发前登记动作意图。","action_id|ID|动作\nbusiness_key?|NonEmptyText|幂等键\nnormalized_arguments_hash|Hash|参数\nprovider_ref|Ref|提供方\nattempt_id|ID|首次尝试"),
      ("CompressionRequest","context","语义压缩保护必要上下文。","input_snapshot_ref|Ref|输入\npreserve|PreservationSpec|保护\ntarget_tokens|PositiveTokenCount|目标大小\nexpected_context_epoch|Revision|纪元"),
      ("CompressionValidateRequest","context","核对压缩后的关键要求、数字和引用。","source_snapshot_ref|Ref|压缩前\nsummary_ref|Ref|摘要\npreserve|PreservationSpec|保护"),
      ("RemoteCapabilityRequest","tool","远端能力规范注册。","session_ref|Ref|session\nremote_capabilities|[](Capability)|远端目录\nexpected_registry_revision|Revision|目录CAS"),
      ("SelectionRequest","context","选择和预算分配，不额外执行所有策略。","candidate_refs|[](Ref)|候选\npurpose|Purpose|目的\nmodel_context_limit|PositiveTokenCount|真实窗口\noutput_reserve|Count|输出\ntool_reserve|Count|往返"),
      ("IngestionPublishRequest","context","摄取完成后原子发布索引。","ingestion_ref|Ref|已核验作业\nexpected_active_revision|Revision|当前索引CAS"),
      ("CacheComputeRequest","support","只合并相同依赖的可信纯计算；各等待者取消独立。","key|CacheKey|缓存键\ncomputation_ref|Ref|服务预注册的只读/纯计算句柄\ndeadline|Timestamp|截止"),
      ("CompletionProposalRequest","agent","核对要求、成果、报告与未知效果后提出完成。","delivery_contract_ref|Ref|验收\nartifact_refs|[](Ref)|成果\nverification_refs|[](Ref)|证据\nexpected_revisions|RevisionMap|参与域修订"),
    ]:record(name,owner,description,spec)
    # The event payload registry is explicit, though envelopes store payload by Ref.
    events=[
      ("input.committed","InputRecord"),("understanding.preview","DraftPreview"),("task.frame.committed","TaskFrame"),
      ("plan.committed","TaskGraph"),("agent.updated","AgentInstance"),("agent.result","AgentResult"),
      ("tool.started","ValidatedCall"),("tool.completed","ToolResult"),("process.updated","ProcessRecord"),
      ("changes.committed","ChangeSet"),("artifact.registered","ArtifactRecord"),("approval.required","ApprovalRequest"),
      ("approval.decided","ApprovalGrant"),("item.delta","ItemPatch"),("item.updated","InteractionItem"),
      ("run.updated","RunRecord"),("verification.completed","VerificationReport"),("control.accepted","Acknowledgement"),
      ("memory.deleted","DeletionReceipt"),("configuration.activated","ConfigurationVersion"),("checkpoint.committed","Checkpoint"),("budget.updated","BudgetReservation"),
    ]
    enum("EventType","|".join(x[0] for x in events),"run")
    tagged_union("EventPayload",[(event,payload,payload) for event,payload in events],"run")
    TYPES["EventEnvelope"]["properties"]["type"]=dict(ref("EventType"),description="注册事件类型；payload_ref解引用后按EventPayload分支校验。")
    TYPES["EventAppendRequest"]["properties"]["event_type"]=dict(ref("EventType"),description="注册事件名；只能发送匹配类型的payload。")
    executed=[o for o in OPERATIONS if o["channel"]=="runner" and o["id"] not in ["pair.begin","pair.complete","heartbeat","root.select"]]
    tagged_union("RunnerParameters",[(o["id"],o["request"],o["response"]) for o in executed],"workspace")
    tagged_union("RunnerSuccessPayload",[(o["id"],o["request"],o["response"]) for o in executed],"workspace",True)
    TYPES["RunnerCommand"]["properties"]["parameters"]=dict(ref("RunnerParameters"),description="签名覆盖的内联参数；action为Runner方法名。")
    TYPES["RunnerCommand"]["required"].append("parameters")
    record("RunnerReceipt","workspace","设备回执不能把启动成功当任务完成。","command_id|ID|对应命令\nattempt_id|ID|实际执行\nkind|RunnerReceiptKind|成功/等待/失败\npayload?|RunnerSuccessPayload|成功结果\nwait_ref?|Ref|等待进程/授权\nfailure?|Failure|失败详情\nusage|Usage|实际消耗\nsignature|NonEmptyText|设备签名")
    enum("RunnerReceiptKind","ok|waiting|failed|cancelled","workspace")
    TYPES["RunnerReceipt"]["allOf"]=[
      {"if":{"properties":{"kind":{"const":"ok"}},"required":["kind"]},"then":{"required":["payload"],"not":{"anyOf":[{"required":["wait_ref"]},{"required":["failure"]}]}}},
      {"if":{"properties":{"kind":{"const":"waiting"}},"required":["kind"]},"then":{"required":["wait_ref"],"not":{"anyOf":[{"required":["payload"]},{"required":["failure"]}]}}},
      {"if":{"properties":{"kind":{"enum":["failed","cancelled"]}},"required":["kind"]},"then":{"required":["failure"],"not":{"anyOf":[{"required":["payload"]},{"required":["wait_ref"]}]}}},
      {"if":{"properties":{"kind":{"const":"cancelled"}},"required":["kind"]},"then":{"properties":{"failure":{"properties":{"category":{"const":"cancelled"}}}}}},
    ]
    enum("ParallelScope","none|tools|agents|mixed","agent")
    enum("DecisionStatus","ready|provisional","agent")
    record("SuggestedDelegation","agent","执行评估中的分工建议，尚未分配预算或启动实例。","definition_ref?|Ref|候选角色\ngoal|NonEmptyText|子目标\ninput_refs|[](Ref)|已知资料\noutput_contract|Contract|验收\nstart_condition|StartCondition|何时可启动")
    enum("StartCondition","inputs_available|after_dependencies","agent")
    for key,kind,note in [("decision_status","DecisionStatus","资料不足时暂定"),("parallel_scope","ParallelScope","工具并发与Agent并发分开"),("suggested_delegations",None,"建议而非已启动")]:
        TYPES["ExecutionAssessment"]["properties"][key]=dict(ref(kind) if kind else arr("SuggestedDelegation",16),description=note)
        TYPES["ExecutionAssessment"]["required"].append(key)
    TYPES["ExecutionAssessment"]["allOf"]=[
      {"if":{"properties":{"parallelism":{"const":"serial"}},"required":["parallelism"]},"then":{"properties":{"parallel_scope":{"const":"none"}}}},
      {"if":{"properties":{"parallelism":{"const":"parallel"}},"required":["parallelism"]},"then":{"properties":{"parallel_scope":{"enum":["tools","agents","mixed"]}}}},
      {"if":{"properties":{"delegation":{"const":"single"}},"required":["delegation"]},"then":{"properties":{"suggested_delegations":{"maxItems":0},"parallel_scope":{"enum":["none","tools"]}}}},
    ]
    # The registry/source draft DTOs intentionally exclude server-assigned revisions.
    record("ConfigurationDraft","support","管理配置业务草案，发布ID/revision/state由服务分配。", "model_refs|[](Ref)|模型目录\nprovider_refs|[](Ref)|提供方\nenvironment_template_refs|[](Ref)|环境模板\nfeature_flags|[](FeatureFlag)|旗标\napproval_policy_ref|Ref|审批政策\nstorage_policy_ref|Ref|部署存储政策")
    TYPES["AdminConfigurationStageRequest"]["properties"]["configuration"]=dict(ref("ConfigurationDraft"),description="待验证配置，不含服务版本。")
    record("ModelRegistration","model","管理员声明模型能力，修订由目录分配。", "id|ID|稳定名称\nprovider_ref|Ref|提供方\ndisplay_name|NonEmptyText|展示名\ncontext_limit_tokens|PositiveTokenCount|窗口\noutput_limit_tokens|PositiveTokenCount|输出上限\ncapabilities|[](ID)|能力")
    scalar("PositiveTokenCount","model","非零Token预算。",type="integer",minimum=1,maximum=10000000)
    scalar("RevisionMap","common","ID到CAS修订映射；键和值均校验。",type="object",additionalProperties=ref("Revision"),maxProperties=256,propertyNames=TYPES["ID"])
    TYPES["AdminModelsRegisterRequest"]["properties"]["entry"]=dict(ref("ModelRegistration"),description="非秘密模型声明。")
    TYPES["ModelCatalogEntry"]["properties"]["pricing_ref"]=dict(ref("Ref"),description="可选固定价格；缺少时账单显式pending/estimated，不填0。")
    for name in ["Conversation","ConversationsCreateRequest"]:
        TYPES[name]["properties"]["approval_mode"]=dict(ref("ApprovalMode"),description="用户选择；不能扩大管理员政策与本机权限。",default="manual")
        if name=="Conversation": TYPES[name]["required"].append("approval_mode")
    TYPES["ConversationPatch"]["properties"]["approval_mode"]=dict(ref("ApprovalMode"),description="审批模式修订，在下一安全边界生效。")
    # Large writes use an already uploaded content reference, never truncate source.
    write=TYPES["ToolFileWriteInput"]
    write["required"].remove("text")
    write["properties"]["content_ref"]=dict(ref("Ref"),description="大内容的获准完整blob；与text互斥。")
    write["oneOf"]=[{"required":["text"],"not":{"required":["content_ref"]}},{"required":["content_ref"],"not":{"required":["text"]}}]
    write["allOf"]=[{"if":{"properties":{"create_only":{"const":False}},"required":["create_only"]},"then":{"required":["expected_content_hash"]}}]
    TYPES["TurnsSubmitRequest"]["allOf"]=[{"if":{"required":["task_id"]},"then":{"required":["expected_task_revision"]}}]
    TYPES["TurnsSubmitRequest"]["anyOf"]=[{"properties":{"text":{"minLength":1}}},{"properties":{"attachment_refs":{"minItems":1}}}]
    TYPES["DefinitionItemResult"]["allOf"]=[{"if":{"properties":{"status":{"enum":["created","updated","unchanged"]}},"required":["status"]},"then":{"required":["definition"],"not":{"required":["failure"]}}},{"if":{"properties":{"status":{"enum":["needs_resolution","failed"]}},"required":["status"]},"then":{"required":["failure"],"not":{"required":["definition"]}}}]
    TYPES["ResolvedModelPolicy"]["properties"]["mode"]={"type":"string","enum":["explicit","auto"],"description":"继承已经解析为父政策模式。"}
    TYPES["ResolvedModelPolicy"]["allOf"]=[{"if":{"properties":{"mode":{"const":"explicit"}},"required":["mode"]},"then":{"required":["fixed_model_id"]}},{"if":{"properties":{"mode":{"const":"auto"}},"required":["mode"]},"then":{"properties":{"allowed_model_ids":{"minItems":1}}}}]
    TYPES["UserControl"]["allOf"]=[{"if":{"properties":{"mode":{"enum":["steer","enqueue","replace"]}},"required":["mode"]},"then":{"required":["input_ref"]}}]
    TYPES["ModelCall"]["allOf"]=[{"if":{"properties":{"output_protocol":{"const":"json_schema"}},"required":["output_protocol"]},"then":{"required":["output_schema"]}}]
    record("ReasoningConfiguration","model","仅使用模型目录支持的提供方推理参数，不索要私密思维链。","level|NonEmptyText|提供方支持的级别\nmax_tokens?|PositiveTokenCount|可选推理上限")
    TYPES["ModelOutput"]["properties"]["content_ref"]=dict(ref("Ref"),description="大输出的完整内容引用。")
    TYPES["ModelOutput"]["properties"]["text_complete"]=dict(ref("Bool"),description="text是否包含本次收到的完整可见文本；不表示整个任务完成。")
    TYPES["ModelOutput"]["required"].append("text_complete")
    TYPES["ModelOutput"]["allOf"]=[{"if":{"properties":{"text_complete":{"const":False}},"required":["text_complete"]},"then":{"required":["content_ref"]}}]
    TYPES["ToolTasksPlanInput"]["oneOf"]=[{"required":["patch"],"properties":{"node_specs":{"maxItems":0}}},{"not":{"required":["patch"]},"properties":{"node_specs":{"minItems":1}}}]
    TYPES["ToolWorkspaceRevertInput"]["properties"]["selected_unit_ids"]["minItems"]=1
    TYPES["WorkspacesMergeRequest"]["properties"]["selected_unit_ids"]["minItems"]=1
    TYPES["WorkspacesRevertRequest"]["properties"]["selected_unit_ids"]["minItems"]=1
    TYPES["MemorySelector"]["minProperties"]=1
    record("AccountConnectionView","support","普通用户连接视图，不返回秘密句柄。", "id|ID|连接\nprovider_ref|Ref|提供方\nstate|ConnectionState|状态\ngranted_scopes|[](ID)|范围\nexpires_at?|Timestamp|期限\nrevision|Revision|版本")
    TYPES["ConnectionPage"]["properties"]["items"]["items"]=ref("AccountConnectionView")
    endpoint("tasks.attach_conversation","POST","/v1/tasks/{task_id}/conversations","run","run.history agent.board run.state","显式把同用户另一会话关联到现有任务。","task_id|ID|共享任务\nconversation_id|ID|目标会话\nsource_input_ref|Ref|用户明确关联要求","TaskRecord","internal_write",["两端同主体且expected_revision匹配；关联不复制权限，不取得写控制权；并发修订CAS冲突。"])
    # Observations may be incomplete after a provider failure. Unknown costs are omitted,
    # never represented by a fabricated zero; reservations retain the corresponding estimate.
    measured=copy.deepcopy(TYPES["ResourceVector"])
    measured["description"]="已观察用量；pending时所有未知维度均省略，币种必需，不能用0代替未知。"
    measured["required"]=["currency"]
    TYPES["MeasuredResources"]=measured;OWNERS["MeasuredResources"]="run"
    RULES["MeasuredResources"]=["缺失项维持预留；确认账单前不能释放未知消耗。"]
    TYPES["Usage"]["properties"]["resources"]=dict(ref("MeasuredResources"),description="真实观察值；未知项省略。")
    TYPES["Usage"]["allOf"]=[{"if":{"properties":{"billing_state":{"enum":["confirmed","estimated"]}},"required":["billing_state"]},"then":{"properties":{"resources":{"required":list(TYPES["ResourceVector"]["required"])}}}},{"if":{"properties":{"billing_state":{"const":"pending"}},"required":["billing_state"]},"then":{"properties":{"resources":{"not":{"required":["money"]}}}}}]
    record("RootBudgetLedger","run","根预算的事务权威；所有attempt与待核对额度保留。","id|ID|账本\nrun_id|ID|运行\nrevision|Revision|CAS\nlimits|ResourceVector|总额\nheld|ResourceVector|尚未确认的额度\nused|ResourceVector|已观察消耗\nbilling_pending|Bool|待确认\noverdrawn|Bool|实际超额\ncancel_requested|Bool|停止新准入\ndeadline|Timestamp|截止")
    record("AttemptTrace","support","脱敏运行观测，不保存输入正文、认证头或秘密。","operation_id|ID|操作\ntrace_id|ID|链路\nattempt_id|ID|尝试\nrun_id|ID|运行\nreservation_ref|Ref|额度\nstatus|NonEmptyText|实际结果\nusage_ref|Ref|实际用量\ncreated_at|Timestamp|记录时间")
    record("ReservationAccounting","run","每个attempt独占预留；发出调用意图后保留未知用量。","run_id|ID|运行\noperation_id|ID|操作\ntrace_id|ID|链路\nattempt_id|ID|尝试\ndeadline|Timestamp|预留截止\ndispatched|Bool|已经提交调用意图\nheld|ResourceVector|待确认额度\nused|ResourceVector|已观察消耗\nbilling_pending|Bool|账单待确认\nusage?|Usage|最近实际观察\nusage_revision?|Revision|用量修订")
    TYPES["ReservationAccounting"]["dependentRequired"]={"usage":["usage_revision"],"usage_revision":["usage"]}
    record("RunAdmissionBinding","run","受理时固定实际来源、用户模型政策和配置。","input_ref|UserInputRef|原始输入\nmodel_policy_ref|Ref|用户选择\nconfiguration_ref|Ref|固定配置\nturn_id|ID|提交轮次")
    record("RunToolAccessBinding","run","可信控制入口登记的Run/Agent工具角色绑定；不是模型可提交的授权。","run_id|ID|实际Run\nagent_id?|ID|单个Agent槽位\nprincipal|Principal|完整用户与认证会话\nscope|Scope|固定执行范围\nmodel_policy_ref|Ref|固定用户模型\ncapability_policy_ref|Ref|实际权限版本\nrole_ref|Ref|实际角色版本及摘要\nenvironment|ID|部署环境\nrevision|Revision|CAS版本\nstate|NonEmptyText|active或revoked")
    TYPES["RunToolAccessBinding"]["properties"]["state"]["enum"]=["active","revoked"]
    RULES["RunToolAccessBinding"]=["仅内部已认证controller可登记/撤销；HTTP和模型工具不接受此对象。", "Run/Agent槽位、完整Principal/session、scope和固定政策逐次匹配。", "角色类别不授权资源，不替换固定模型；当前Run/权限/配置/提供方均须复查。"]
    record("AgentRootBinding","agent","内部根实例固定创建来源，不从模型参数取得认证或角色权限。","context|TrustedExecutionContext|完整拥有者和执行范围\nstart_request|AgentStartRequest|原创建参数\nrole_ref|Ref|实际角色版本\nmax_steps|Revision|有界步数上限")
    record("AgentLoopState","agent","自有CAS状态；框架检查点不替代此权威。","instance_id|ID|根实例\nrevision|Revision|CAS\nsteps|Revision|已认领模型步骤\nframe_ref|Ref|当前任务理解\nobservation_refs|[](Ref)|已登记观察\nactive_operation_ref?|Ref|原步骤持久意图")
    record("AgentDecision","agent","固定模型的有界建议，无完成或执行授权。","action|AgentStepAction|拟采取动作\ntext|Text|答复或解释\nproposed_calls|[](ToolCall)|至多一个待授权工具")
    TYPES["AgentDecision"]["properties"]["text"].update(maxLength=16384)
    TYPES["AgentDecision"]["properties"]["proposed_calls"].update(maxItems=1)
    enum("AgentOperationPhase","claimed|prepared|decided|waiting|finished|failed","agent")
    record("AgentLoopOperation","agent","原步骤及原模型/工具尝试，恢复不换ID重新发送。","id|ID|操作\ninstance_id|ID|根实例\nrevision|Revision|CAS\nstep|Revision|步数\nrequest|AgentStepRequest|固定请求\ncontext|TrustedExecutionContext|原模型尝试\nphase|AgentOperationPhase|持久阶段\nsnapshot_ref?|Ref|实际上下文快照\ncontext_epoch?|Revision|实际快照纪元，不是模型步数\nmodel_request?|ModelCall|原模型调用\nmodel_result?|RuntimeModelruntimeGenerateResult|实际模型回执\nproposal?|AgentDecision|已验证建议\ntool_context?|TrustedExecutionContext|原工具尝试\nobservation_ref?|Ref|登记结果\nresult?|RuntimeAgentruntimeStepResult|实际步骤结果")
    record("AgentObservation","agent","保存真实工具返回和原调用；失败也进入下一轮观察。","context|TrustedExecutionContext|完整来源绑定\ncall|ToolCall|实际调用\nresult|RuntimeToolruntimeInvokeResult|实际成功等待或失败")
    record("AgentContextPreparation","agent","原步骤的上下文登记意图；恢复保持原配方CAS参数。","context|TrustedExecutionContext|原步骤上下文\nrequest|ContextRequest|固定配方参数\nrules|InternalContextRulesRequest|固定规则选择\ntools|ModelToolSet|真实工具集合\nrevision|Revision|CAS\nsnapshot_ref?|Ref|实际构建后快照")
    for name in ["AgentRootBinding","AgentLoopState","AgentLoopOperation","AgentObservation"]:
        RULES[name]=["仅可信内部适配器写入，当前拥有者/session/Run/固定模型/角色和资源逐次复查。", "不证明框架END、模型建议或传输成功已经完成用户任务。"]
    record("ApprovalBinding","run","审批内部权威绑定；只由Run/获准Tool适配器构造，不接受模型或HTTP提供可信上下文。","context|TrustedExecutionContext|固定主体、Run、动作上下文\nrequest|ApprovalCreateRequest|固定动作参数摘要、资源和效果\nconfiguration_ref|Ref|Run受理配置\napproval_policy_ref|Ref|固定审批政策")
    record("ExecutionPolicySnapshot","run","实时父子权限交集，非可复用授权；来源均为当前主体持久政策。","run_id|ID|已受理运行\nscope|Scope|当前可信请求作用域\npolicy_refs|[](Ref)|叶到根当前版本与摘要\nallowed_capabilities|[](ID)|在全部父政策允许的当前scope能力\ndenied_capabilities|[](ID)|祖先显式禁止的并集\nnetwork_allowlist|[](NonEmptyText)|网络范围交集\nfeature_flag_refs|[](Ref)|需另行核验的开关引用",["不创建权限、不证明角色/设备/资源/租约或执行器已就绪；模型不能提供该对象来取得授权；执行前必须重查当前状态。"])
    TYPES["ExecutionPolicySnapshot"]["properties"]["policy_refs"].update(minItems=1,maxItems=8)
    TYPES["ExecutionPolicySnapshot"]["properties"]["allowed_capabilities"].update(minItems=1)
    TYPES["ExecutionPolicySnapshot"]["properties"]["policy_refs"]["items"]={"allOf":[ref("Ref"),{"properties":{"kind":{"const":"policy"},"version":{"pattern":"^[1-9][0-9]*$"}},"required":["content_hash"],"not":{"anyOf":[{"required":["location"]},{"required":["access_scope"]}]}}]}
    record("CredentialMetadata","support","不含密文或明文秘密的句柄归属。","provider_id|ID|提供方\nreceipt|SecretReceipt|回执")
    record("ModelHttpSettings","support","首批HTTP模型配置profile；注册不意味着完成连通或协议适配。","model_name|NonEmptyText|提供方模型名称\ntimeout_ms|Duration|超时")
    TYPES["ModelHttpSettings"]["properties"]["timeout_ms"].update(minimum=1000,maximum=300000)
    record("ModelChatCompletionsSettings","support","显式Chat Completions协议；预留金额不是价格或实际账单。","model_name|NonEmptyText|固定供应商模型\ntimeout_ms|Duration|总调用上限\noutput_token_parameter|NonEmptyText|供应商输出额度字段\nreservation_money|Decimal|每attempt的管理员预留额度\nallow_temperature|Bool|是否支持temperature\nallowed_response_models?|[](NonEmptyText)|批准的同模型响应别名\nreasoning_levels?|[](NonEmptyText)|批准的推理档位\nstructured_output_mode?|NonEmptyText|json_schema原生严格模式或json_object加UAW本地schema校验；默认原生模式，不自动降级\ninclude_n?|Bool|是否发送n=1；省略时保留旧行为\ndefault_reasoning_level?|NonEmptyText|管理员批准的默认推理档位，必须属于reasoning_levels，记入实际配置")
    TYPES["ModelChatCompletionsSettings"]["properties"]["timeout_ms"].update(minimum=1000,maximum=300000)
    TYPES["ModelChatCompletionsSettings"]["properties"]["output_token_parameter"]["enum"]=["max_completion_tokens","max_tokens"]
    TYPES["ModelChatCompletionsSettings"]["properties"]["structured_output_mode"]["enum"]=["json_schema","json_object"]
    record("ModelInvocation","model","持久调用意图；claimed重读不能再发送，finished只重放保存的回执。","id|ID|逻辑调用\nrun_id|ID|运行\nrequest_hash|Hash|精确请求及可信关联摘要\nrequest|ModelCall|固定输入引用、配置与协议\noperation_id|ID|操作\ntrace_id|ID|链路\nstate|NonEmptyText|claimed或finished\nresult?|Object|已校验的Runtime结果\ncreated_at|Timestamp|受理时间")
    TYPES["ModelInvocation"]["properties"]["state"]["enum"]=["claimed","finished"]
    TYPES["ModelInvocation"]["allOf"]=[{"if":{"properties":{"state":{"const":"finished"}},"required":["state"]},"then":{"required":["result"]}}]
    record("ModelAttemptRecord","model","每次真实发送的固定配置、原始响应引用与观察用量；秘密不进入记录。","id|ID|尝试\nrun_id|ID|运行\ninvocation_id|ID|逻辑调用\nactual_config|ResolvedModelConfig|固定实际配置\nstate|NonEmptyText|dispatched、received或failed\nusage?|Usage|实际观察\nresponse_ref?|Ref|完整成功HTTP响应\noutput_ref?|Ref|完整模型文本\nfailure?|Failure|脱敏错误\ncreated_at|Timestamp|发送意图时间")
    TYPES["ModelAttemptRecord"]["properties"]["state"]["enum"]=["prepared","dispatched","received","failed"]
    record("ModelContextBinding","context","私有输入快照与Run/会话的归属绑定；不从Ref推断权限。","snapshot_ref|Ref|固定快照\nrun_id|ID|运行\nconversation_id|ID|会话")
    record("ModelToolSet","tool","由可信工具发现层提供的固定工具定义；本轮诊断输入为空。","run_id|ID|运行\ntools|[](ToolSpec)|获准候选工具")
    for name in ["provider_model_name","response_model_name"]:
        TYPES["ResolvedModelConfig"]["properties"][name]=dict(ref("NonEmptyText"),description="实际供应商请求/响应模型名称；别名需管理员批准。")
    TYPES["RefKind"]["enum"].extend(["model","provider_profile"])
    for name,kind in [("ModelRef","model"),("ProviderProfileRef","provider_profile")]:
        TYPES[name]={"allOf":[ref("Ref"),{"properties":{"kind":{"const":kind}}}]}
        OWNERS[name]="support";RULES[name]=["引用由所属目录解析并验证实际固定版本。"]
    TYPES["ProviderDraft"]["properties"]["profile_ref"]["$ref"]="#/$defs/ProviderProfileRef"
    for name in ["ConfigurationVersion","ConfigurationDraft"]:
        TYPES[name]["properties"]["model_refs"]["items"]=ref("ModelRef")
    endpoint("admin.providers.revoke","DELETE","/v1/admin/providers/{provider_id}","support","support.configuration","撤销提供方，固定旧配置不能绕过当前撤销。","provider_id|ID|提供方","ProviderBinding","internal_write",["管理员认证与expected_revision必需；不撤销已发生的外部动作。"],auth="admin")
    endpoint("events.payload","GET","/v1/events/{event_id}/payload","run","run.events","读取同主体持久事件的严格分支载荷。","event_id|ID|事件","EventPayload")
    for operation in OPERATIONS:
        if operation["id"]=="admin.configuration.validate":
            operation["effect"]="internal_write"
            operation["rules"].append("expected_revision必需；结构与引用校验成功后提交validated修订，不执行网络探测。")
    from implementation_catalog import IMPLEMENTATIONS
    for operation in OPERATIONS:
        if operation["id"] in IMPLEMENTATIONS:
            operation["implemented"]=True
            operation["implementation"]=IMPLEMENTATIONS[operation["id"]]
    # Internal persisted bindings; they do not open an HTTP or model-tool entry.
    record("EvaluationSourcePin", "model", "评估器实际读取的对象版本与命名空间。",
           "namespace|ID|实际存储命名空间\nref|Ref|固定版本和完整行摘要\nschema_name|ID|对象结构名称")
    obj("EvaluationInputBinding", "model", "有界评估输入；固定用户模型且不递归展开Context。", {
        "id": field("ID", "原评估操作身份"),
        "revision": field("Revision", "不可变输入版本"),
        "context": field("TrustedExecutionContext", "可信完整运行关联"),
        "frame_ref": field("Ref", "实际TaskFrame版本和摘要"),
        "role_ref": field("Ref", "实际角色版本"),
        "sources": field(arr("EvaluationSourcePin", 128), "实际对象来源"),
        "instruction": field("NonEmptyText", "评估职责指令"),
        "data": field("Object", "TaskFrame与该职责的候选内容"),
    }, ["总输入最多96KiB；读取和派发前复查当前来源。模型输出不授予权限。"])
    obj("ArtifactSourceBinding", "workspace", "实际文本成果的原模型输出及工具观察归属。", {
        "context": field("TrustedExecutionContext", "可信完整运行关联"),
        "frame_ref": field("Ref", "原TaskFrame"),
        "model_output_ref": field("Ref", "已完成实际ModelOutput"),
        "observation_refs": field(arr("Ref", 128), "实际工具观察"),
    }, ["与ArtifactRecord原子登记；只支持最多64KiB的实际UTF-8文本或Markdown。"])
    obj("CompletionBundle", "agent", "不可变成果、合同、报告和完成提案的版本关联。", {
        "id": field("ID", "原Agent操作派生身份"),
        "context": field("TrustedExecutionContext", "可信完整运行关联"),
        "instance_id": field("ID", "原Agent实例"),
        "frame_ref": field("Ref", "实际TaskFrame"),
        "contract_ref": field("Ref", "原文、约束和输出要求形成的合同"),
        "artifact_ref": field("Ref", "实际成果"),
        "report_ref": field("Ref", "逐项VerificationReport"),
        "proposal_ref": field("Ref", "候选DeliveryProposal"),
        "source_pins": field(arr("EvaluationSourcePin", 128), "终态前重新读取的实际来源"),
        "tool_activity_ids": field(arr("ID", 16), "评估时该Run所有已登记工具动作；终态再核对完整集合", True),
    }, ["Bundle本身不是写权限；独立控制器以当前Run版本提交终态。"])
    record("CompletionAcceptance", "run", "独立认证用户对确切成果版本的审阅记录。",
           "bundle_ref|Ref|确切不可变交付Bundle\nprincipal|Principal|真实认证用户\ndecision|DeliveryDecision|用户决定\ncreated_at|Timestamp|实际登记时间",
           ["当前入口只登记一次；只有accept可满足需要用户接受的合同，拒绝/修订/部分接受不完成Run。"])
    register_private_components(graph,strategies)
    for name,s in TYPES.items():
        for key,value in s.get("properties",{}).items():
            if key in ["source_input_ref","user_source_ref","user_input_ref","original_input_ref"] and value.get("$ref")=="#/$defs/Ref":value["$ref"]="#/$defs/UserInputRef"
    TYPES["InternalModelAdaptersRequest"]["properties"]["reasoning_config"]=dict(ref("ReasoningConfiguration"),description="支持的推理配置，不接受任意Object或用户模型替换。")
    TYPES["InternalContextRetrievalRequest"]["properties"]["max_age_ms"]=dict(ref("Duration"),description="bounded_age必需；0表示不接受陈旧数据。")
    TYPES["InternalContextRetrievalRequest"]["allOf"]=[{"if":{"properties":{"freshness":{"const":"bounded_age"}},"required":["freshness"]},"then":{"required":["max_age_ms"]}}]
    # Normalize older strategy spellings into defined types.
    for name,target in [("Requirement","Requirement"),("PathRef","Ref"),("Schema","Schema")]:
        if name not in TYPES: alias(name,target)
    # Preserve supplied signature fields while adding enforceable numeric bounds.
    for name,schema in TYPES.items():
        if not name.startswith("Internal"): continue
        for key,value in schema.get("properties",{}).items():
            if key in ["top_k","max_candidates","max_calls","target_tokens","lease_ttl"]:
                value.pop("$ref",None); value.update(type="integer",minimum=1,maximum=64 if key in ["top_k","max_candidates","max_calls"] else 604800000)
    # Each operation receives a strict discriminated result object and HTTP envelope.
    for op in OPERATIONS:
        stem="".join(x.capitalize() for x in (op["channel"]+"."+op["id"]).replace("_",".").split("."))
        result=stem+"Result"
        obj(result,op["owner"],"该接口的状态结果；ok才携带完整业务payload。",{
          "kind":field({"type":"string","enum":["ok","waiting","missing","denied","conflict","stale","failed","cancelled"]},"接口状态"),
          "payload":field(op["response"],"ok的业务结果",True),
          "output_refs":field(arr("Ref"),"关联真实资源"),
          "revision":field("Revision","本次提交/读取的域版本",True),
          "failure":field("Failure","失败状态的明确原因",True),
          "wait_ref":field("Ref","waiting时审批/进程/用户问题引用",True),
          "usage_ref":field("Ref","发生消耗时真实统计",True)},
          ["ok必需payload且不含failure；waiting必需wait_ref；其他状态必需failure；取消不回滚已确认外部动作。"])
        TYPES[result]["allOf"]=[
          {"if":{"properties":{"kind":{"const":"ok"}},"required":["kind"]},"then":{"required":["payload"],"not":{"required":["failure"]}}},
          {"if":{"properties":{"kind":{"const":"waiting"}},"required":["kind"]},"then":{"required":["wait_ref"],"not":{"required":["payload"]}}},
          {"if":{"properties":{"kind":{"enum":["missing","denied","conflict","stale","failed","cancelled"]}},"required":["kind"]},"then":{"required":["failure"],"not":{"required":["payload"]}}},
        ]
        op["result"]=result
        if op["channel"]=="http":
            envelope=stem+"Envelope"
            obj(envelope,op["owner"],"HTTP请求meta和业务参数；路径/查询另由API合成。",{
                "meta":field("RequestMeta","幂等与版本元信息"),"payload":field(op["request"],"业务参数")})
            op["envelope"]=envelope
    return TYPES,OPERATIONS
