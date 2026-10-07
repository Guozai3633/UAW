"""Generate reviewable contracts and per-interface/type documentation, not backend code."""
from pathlib import Path
import copy, json, re, sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from contracts.interface_catalog import TYPES,OWNERS,RULES,OPERATIONS,finalize
from design.catalog import STRATEGIES

GRAPH=json.loads((ROOT/"architecture/graph.json").read_text(encoding="utf-8"))
finalize(GRAPH,STRATEGIES)
OUT=ROOT/"docs/api"
CHANNELS={"http":"用户与管理端 HTTP API","tool":"模型可调用工具","runner":"本地 Runner 协议","runtime":"Runtime 公共入口","component":"细分组件私有接口"}
OWNERNAMES={"common":"公共协议","intent":"任务理解","agent":"Agent执行与协作","context":"上下文与资料","tool":"工具运行","workspace":"工作区与交付","model":"模型调用","run":"运行与会话","support":"配置与共享基础设施"}

def write(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(data if isinstance(data,str) else json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

def rewrite_refs(value,prefix):
    if isinstance(value,dict):
        return {k:(prefix+v[8:] if k=="$ref" and isinstance(v,str) and v.startswith("#/$defs/") else rewrite_refs(v,prefix)) for k,v in value.items()}
    if isinstance(value,list):return [rewrite_refs(v,prefix) for v in value]
    return value

def slug(op):return op["channel"]+"--"+op["id"].replace(".","-").replace("_","-")
def operation_name(op):return op["channel"]+"_"+re.sub(r"[^A-Za-z0-9_]","_",op["id"])
def schema_link(name,base="../objects/"):return f"[{name}]({base}{name}.md)"

def type_label(schema,base="../objects/"):
    if "$ref" in schema:return schema_link(schema["$ref"].split("/")[-1],base)
    if "const" in schema:return "常量 `"+str(schema["const"])+"`"
    if "enum" in schema:return "enum: "+" / ".join(f"`{v}`" for v in schema["enum"])
    if schema.get("type")=="array":return "数组&lt;"+type_label(schema["items"],base)+"&gt;"
    if schema.get("type")=="object" and isinstance(schema.get("additionalProperties"),dict):return "映射&lt;string, "+type_label(schema["additionalProperties"],base)+"&gt;"
    if "oneOf" in schema or "anyOf" in schema:return "互斥选择" if "oneOf" in schema else "至少一个分支"
    return str(schema.get("type","见结构规则"))

def constraints(schema):
    notes=[]
    for key,label in [("minimum","≥"),("maximum","≤"),("minLength","最少字符"),("maxLength","最多字符"),("minItems","最少项"),("maxItems","最多项"),("maxProperties","最多键"),("minProperties","最少字段"),("pattern","正则"),("format","格式"),("uniqueItems","去重"),("default","默认注解"),("writeOnly","仅写")]:
        if key in schema:notes.append(f"{label} `{schema[key]}`")
    if "$ref" in schema:notes.append("类型约束见对应对象")
    if isinstance(schema.get("additionalProperties"),dict):notes.append("值逐项按schema校验")
    if schema.get("additionalProperties") is False:notes.append("拒绝未声明字段")
    return "；".join(notes) or "—"

# Shape examples are illustrative. Business-state validation is a separate gate.
def resolve(schema):
    target=copy.deepcopy(schema);seen=set()
    while "$ref" in target:
        name=target["$ref"].split("/")[-1]
        if name in seen:raise ValueError("recursive root alias "+name)
        seen.add(name)
        siblings={k:v for k,v in target.items() if k!="$ref"}
        target=copy.deepcopy(TYPES[name]);target.update(siblings)
    return target

def merge_schemas(a,b):
    a=resolve(a);b=resolve(b);result=copy.deepcopy(a)
    for k,v in b.items():
        if k=="properties":
            result.setdefault(k,{})
            for f,s in v.items():result[k][f]=merge_schemas(result[k][f],s) if f in result[k] else copy.deepcopy(s)
        elif k=="required":result[k]=list(dict.fromkeys(result.get(k,[])+v))
        elif k=="items" and isinstance(v,dict):result[k]=merge_schemas(result[k],v) if k in result else copy.deepcopy(v)
        else:result[k]=copy.deepcopy(v)
    return result

def basic_matches(data,condition):
    if isinstance(data,dict):
        if any(k not in data for k in condition.get("required",[])):return False
        for k,s in condition.get("properties",{}).items():
            if k in data:
                if "const" in s and data[k]!=s["const"]:return False
                if "enum" in s and data[k] not in s["enum"]:return False
        return True
    return False

def example(schema,depth=0):
    if depth>35:raise ValueError("recursive required data")
    s=resolve(schema)
    if "const" in s:return s["const"]
    if "enum" in s:return s["enum"][0]
    if "oneOf" in s or "anyOf" in s:
        key="oneOf" if "oneOf" in s else "anyOf"
        base={k:v for k,v in s.items() if k!=key}
        # Pick the first non-not-only alternative; negative assertions never add fields.
        branch=s[key][0]
        return example(merge_schemas(base,branch),depth+1)
    kind=s.get("type","object")
    if kind=="null":return None
    if kind=="boolean":return True
    if kind in ["integer","number"]:return s.get("minimum",0)
    if kind=="string":
        if s.get("format")=="date-time":return "2026-10-07T02:00:00Z"
        if s.get("format")=="uri":return "https://example.org/resource"
        if s.get("pattern")=="^[a-f0-9]{64}$":return "a"*64
        if s.get("pattern")=="^[1-9][0-9]*$":return "1"
        if "^[A-Z]{3}$"==s.get("pattern"):return "CNY"
        if s.get("pattern","").startswith("^(0|"):return "0"
        if s.get("pattern","").startswith("^(?!"):return "src/main.py"
        value="example_001"
        if s.get("writeOnly"):value="EXAMPLE_ONLY_SECRET"
        return value[:s.get("maxLength",len(value))]
    if kind=="array":
        return [example(s["items"],depth+1) for _ in range(s.get("minItems",0))]
    data={k:example(s.get("properties",{}).get(k,{}),depth+1) for k in s.get("required",[])}
    if not data and s.get("minProperties",0)>0:
        key=next(iter(s.get("properties",{})))
        data[key]=example(s["properties"][key],depth+1)
    amended=copy.deepcopy(s);amended.pop("allOf",None)
    for clause in s.get("allOf",[]):
        if "if" in clause and basic_matches(data,clause["if"]):
            amended=merge_schemas(amended,clause.get("then",{}))
            data.update(example(amended,depth+1))
        elif "if" not in clause:
            amended=merge_schemas(amended,clause)
            data.update(example(amended,depth+1))
    return data

def ref_example(kind,id,version="1"):
    return {"kind":kind,"id":id,"version":version}
USER=ref_example("input","input_create_roles")
CONTRACT={"goal":"核对API兼容性并交付证据","requirements":[{"id":"req_compatibility","text":"说明兼容风险并引用调用方证据","mandatory":True,"source_refs":[USER]}],"outputs":[{"id":"out_report","kind":"markdown","description":"含证据的检查报告","required":True}],"version":"1"}
BUDGET={"limits":{"input_tokens":60000,"output_tokens":12000,"model_calls":12,"tool_calls":30,"child_agents":0,"wall_time_ms":600000,"money":"10.00","currency":"CNY"},"max_steps":20,"max_depth":0,"deadline":"2026-10-07T02:10:00Z"}
DEFINITION={"client_definition_key":"api_reviewer_v1","name":"API兼容性审查员","description":"读取代码及调用方，整理兼容风险和证据","instructions":"先读取接口及调用方，再核对行为差异。证据不足时明确说明，不改动文件。","use_when":["独立核对API兼容性"],"avoid_when":["需要实际修改代码"],"skill_refs":[],"tool_categories":["file_read","code_search"],"input_contract":CONTRACT,"output_contract":CONTRACT,"model_request":{"mode":"inherit"}}
REAL_EXAMPLES={
 "ToolAgentsCreateInput":{"definitions":[DEFINITION],"batch_policy":"atomic","source_input_ref":USER},
 "ToolAgentsInvokeInput":{"delegation":{"goal":"核对本次API修改是否影响已有调用方","input_refs":[ref_example("workspace","workspace_main","tree_7")],"definition_ref":ref_example("agent_definition","agent_api_reviewer","2"),"output_contract":CONTRACT,"budget":BUDGET,"read_refs":[ref_example("workspace","workspace_main","tree_7")],"write_refs":[],"creation_key":"review_api_change_7"}},
 "ToolProcessExecInput":{"spec":{"workspace_ref":ref_example("workspace","workspace_main","tree_7"),"executable":"go","argv":["test","./..."],"cwd":".","environment":[],"timeout_ms":120000}},
 "ToolFileWriteInput":{"workspace_ref":ref_example("workspace","workspace_main","tree_7"),"path":"src/main.py","text":"print('hello')\n","expected_content_hash":"a"*64,"create_only":False},
 "ToolWorkspaceRevertInput":{"workspace_ref":ref_example("workspace","workspace_main","tree_8"),"change_set_ref":ref_example("changeset","changes_8"),"selected_unit_ids":["unit_main_1"],"expected_workspace_version":"tree_8"},
 "ExecutionAssessment":{"planning":"steps","delegation":"single","parallelism":"parallel","information_state":"read_materials","rationale":"先并发只读检索接口与调用方；是否委派需读完材料后再判断。","candidate_agent_refs":[],"independent_groups":[],"reassessment_conditions":["读取实现和调用方后"],"source_frame_ref":ref_example("task_frame","task_api_1"),"decision_status":"provisional","parallel_scope":"tools","suggested_delegations":[]},
 "ConversationsCreateRequest":{"title":"API兼容检查","model_choice":{"mode":"explicit","model_id":"model_user_selected"},"memory_policy":{"revision":0,"read_enabled":False,"contribute_enabled":False,"scope":{"conversation_id":"new_conversation"}},"approval_mode":"manual"},
 "TurnsSubmitRequest":{"conversation_id":"conversation_1","text":"帮我检查这次API修改的兼容性，运行已有测试，保留我的未提交修改。","attachment_refs":[]},
}

EXAMPLES={name:copy.deepcopy(REAL_EXAMPLES.get(name)) if name in REAL_EXAMPLES else example(ref_schema) for name,ref_schema in TYPES.items()}

def body_schema(op):
    s=copy.deepcopy(TYPES[op["request"]]);pathkeys=re.findall(r"{([^}]+)}",op["path"])
    for key in pathkeys:s["properties"].pop(key,None)
    s["required"]=[k for k in s.get("required",[]) if k not in pathkeys]
    return s

def http_parameters(op):
    s=TYPES[op["request"]];pathkeys=re.findall(r"{([^}]+)}",op["path"])
    parameters=[{"name":k,"in":"path","required":True,"schema":rewrite_refs(s["properties"][k],"#/components/schemas/")} for k in pathkeys]
    if op["method"] in ["GET","DELETE"]:
        for k,value in s["properties"].items():
            if k in pathkeys:continue
            parameters.append({"name":k,"in":"query","required":k in s.get("required",[]),"schema":rewrite_refs(value,"#/components/schemas/")})
        parameters += [{"name":"X-Request-Id","in":"header","required":op["method"]=="DELETE","schema":{"$ref":"#/components/schemas/ID"}},
                       {"name":"X-UAW-Schema-Version","in":"header","required":False,"schema":{"type":"string","const":"0.1"}}]
        if op["method"]=="DELETE":parameters.append({"name":"If-Match","in":"header","required":True,"schema":{"type":"string","pattern":"^\"[0-9]+\"$"}})
    if op["id"]=="events.stream":parameters.append({"name":"Last-Event-ID","in":"header","required":False,"schema":{"$ref":"#/components/schemas/Cursor"}})
    return parameters

schema={"$schema":"https://json-schema.org/draft/2020-12/schema","$id":"urn:uaw:contracts:0.1","title":"UAW接口对象0.1（实现范围按接口记录）","$defs":TYPES}
write(ROOT/"contracts/uaw.schema.json",schema)
legacy=ROOT/"contracts/legacy/execution_assessment.v0.1.schema.json"
old=ROOT/"contracts/execution_assessment.schema.json"
if not legacy.exists() and old.exists():
    old_data=json.loads(old.read_text(encoding="utf-8"))
    old_data["deprecated"]=True
    old_data["description"]="Historical experiment; current contract is uaw.schema.json#/$defs/ExecutionAssessment."
    write(legacy,old_data)
write(old,{"$schema":schema["$schema"],"title":"UAW 当前ExecutionAssessment契约入口","description":"与统一对象字典相同，不维护第二套字段。旧实验见legacy/execution_assessment.v0.1.schema.json。","$ref":"uaw.schema.json#/$defs/ExecutionAssessment"})
write(ROOT/"contracts/interfaces.json",{"contract_version":"0.1","architecture_version":GRAPH["architecture_version"],"status":"partial_development_implementation","operations":OPERATIONS})
write(ROOT/"contracts/examples.json",{"status":"shape_examples_not_executable_requests","examples":EXAMPLES})

openapi={"openapi":"3.1.1","jsonSchemaDialect":"https://json-schema.org/draft/2020-12/schema","info":{"title":"UAW功能接口设计","version":"0.1.0","description":"设计目标；无已部署后端。云/本地权威存储方案待确认。"},"paths":{},"components":{"schemas":rewrite_refs(TYPES,"#/components/schemas/"),"securitySchemes":{"sessionAuth":{"type":"http","scheme":"bearer","description":"部署时由账号会话适配器签发；Cookie方案尚待产品决定。"},"adminAuth":{"type":"http","scheme":"bearer","description":"服务端核验admin角色，不接受请求体自报。"}}},"security":[{"sessionAuth":[]}]}

status_map={"202":"waiting","403":"denied","404":"missing","409":"conflict","412":"stale","422":"failed","429":"failed","500":"failed","502":"failed","504":"failed"}
for op in OPERATIONS:
    if op["channel"]!="http":continue
    resultref={"$ref":"#/components/schemas/"+op["result"]}
    result_ok={"allOf":[resultref,{"properties":{"kind":{"const":"ok"}}}]}
    wire={"operationId":operation_name(op),"summary":TYPES[op["request"]]["description"],"tags":[op["owner"]],"parameters":http_parameters(op),"responses":{"200":{"description":"本接口成功；Run/作业可能仍在执行。","content":{"application/json":{"schema":result_ok}}}},"security":[{"adminAuth" if op["auth"]=="admin" else "sessionAuth":[]}],"x-uaw-effect":op["effect"],"x-uaw-node-ids":op["nodes"],"x-uaw-implemented":op["implemented"],"x-uaw-implementation-scope":op.get("implementation",{}).get("scope","planned")}
    if op["method"] not in ["GET","DELETE"]:
        cas=op["method"]=="PATCH" or op["id"] in ["runs.control","runs.checkpoint","runs.resume","approvals.decide","definitions.revert","workspaces.merge","workspaces.revert","reviews.decide","admin.configuration.activate","admin.extensions.activate","admin.extensions.rollback","tasks.attach_conversation"]
        meta={"allOf":[{"$ref":"#/components/schemas/RequestMeta"},{"required":["expected_revision"],"properties":{"expected_revision":{"type":"integer","minimum":1}}}]} if cas else {"$ref":"#/components/schemas/RequestMeta"}
        wire["requestBody"]={"required":True,"content":{"application/json":{"schema":{"type":"object","additionalProperties":False,"required":["meta","payload"],"properties":{"meta":meta,"payload":rewrite_refs(body_schema(op),"#/components/schemas/")}}}}}
        wire["x-uaw-cas-required"]=cas
    for code,kind in status_map.items():
        wire["responses"][code]={"description":kind+"；failure.code区分原因，waiting含wait_ref。","content":{"application/json":{"schema":{"allOf":[resultref,{"properties":{"kind":{"const":kind}}}]}}}}
    wire["responses"]["401"]={"description":"认证失败；不进入业务接口。","content":{"application/json":{"schema":{"$ref":"#/components/schemas/AuthenticationFailure"}}}}
    if op["id"]=="events.stream":
        wire["responses"]["200"]={"description":"SSE事件流；每个data字段JSON为EventEnvelope。","content":{"text/event-stream":{"schema":{"type":"string"}}}}
        wire["responses"]["410"]={"description":"续接位置已回收；先读取快照/交互项后续接。","content":{"application/json":{"schema":{"allOf":[resultref,{"properties":{"kind":{"const":"stale"}}}]}}}}
    openapi["paths"].setdefault(op["path"],{})[op["method"].lower()]=wire
# Authentication failures are defined in the same dictionary as all business DTOs.
write(ROOT/"contracts/openapi.json",openapi)
# A consumer resolves the local dictionary once and projects only input fields.
write(ROOT/"contracts/tools.json",{"version":"0.1","status":"design_only","trusted_context":"separate_and_not_model_visible","tools":[{"name":o["id"],"description":TYPES[o["request"]]["description"],"parameters":{"$ref":"uaw.schema.json#/$defs/"+o["request"]},"result_schema":{"$ref":"uaw.schema.json#/$defs/"+o["result"]},"effect":o["effect"],"feature_flag":o["feature"],"owner":o["owner"]} for o in OPERATIONS if o["channel"]=="tool"]})

def fenced(data):return "```json\n"+json.dumps(data,ensure_ascii=False,indent=2)+"\n```"

for name,s in TYPES.items():
    text=f"# {name}\n\n状态：对象契约0.1；可用范围见具体接口与实施记录。所属：{OWNERNAMES[OWNERS[name]]}。\n\n{s.get('description','')}\n\n[对象总索引](../OBJECTS.md) · [接口总入口](../README.md)\n\n"
    if "properties" in s:
        text+="## 字段\n\n| 字段 | 类型 | 必填 | 含义 | 结构约束 |\n| --- | --- | --- | --- | --- |\n"
        for k,v in s["properties"].items():text+=f"| `{k}` | {type_label(v,'./')} | {'是' if k in s.get('required',[]) else '否'} | {v.get('description','见类型说明').replace('|','／')} | {constraints(v).replace('|','／')} |\n"
    else:text+="## 类型\n\n"+type_label(s,"./")+"。"+constraints(s)+"\n"
    if s.get("additionalProperties") is False:text+="\n拒绝未声明字段。可选字段省略表示没有提供；只有显式 `null` 分支允许空值。默认注解不会自动写入请求。\n"
    for key in ["oneOf","anyOf","allOf","not","dependentRequired","propertyNames"]:
        if key in s:text+="\n## "+key+"结构规则\n\n"+fenced({key:s[key]})+"\n"
    if RULES.get(name):text+="\n## 运行时约束\n\n"+"\n".join("- "+r for r in RULES[name])+"\n"
    text+="\n## 结构示例\n\n以下示例通过类型校验，用于说明结构；引用ID、时间、权限和当前版本仍须由实际运行生成。它不是已执行结果。\n\n"+fenced(EXAMPLES[name])+"\n"
    text+="\n## 机器契约\n\n[统一JSON Schema](../../../contracts/uaw.schema.json)，定位 `$defs."+name+"`。\n"
    write(OUT/"objects"/(name+".md"),text)

node_map={node:{"interfaces":[],"design_doc":value.get("design_doc"),"code_target":value.get("code_target")} for node,value in GRAPH["nodes"].items()}
for op in OPERATIONS:
    for node in op["nodes"]:node_map[node]["interfaces"].append({"id":op["id"],"channel":op["channel"],"doc":"docs/api/interfaces/"+slug(op)+".md"})
for node,info in node_map.items():
    info["interface_doc"]="docs/api/nodes/"+node+".md"
    if not info["interfaces"]:
        info["aggregation_only"]=True
        info["interfaces"]=[i for child,value in node_map.items() if child.startswith(node+".") for i in value["interfaces"]]
for op in OPERATIONS:
    scopes={"development_model_protocol":"模型网关/协议已实现；真实LLM提供方验收待配置",
            "development_intent_protocol":"有来源的理解协议已实现；真实模型语义质量待验收"}
    status=scopes.get(op.get("implementation",{}).get("scope"),"已实现本机开发控制层；Agent执行尚未接入") if op["implemented"] else "契约0.1，待实现"
    inp=TYPES[op["request"]]; text=f"# {op['id']}\n\n状态：{status}。类别：{CHANNELS[op['channel']]}。所属：{OWNERNAMES[op['owner']]}。\n\n{inp.get('description','')}\n\n[分类索引](../{op['channel'].upper()}.md) · [统一规则](../CONVENTIONS.md) · [实际范围](../../implementation/README.md)\n\n## 调用入口\n\n"
    if op["channel"]=="http":
        text+=f"`{op['method']} {op['path']}`；认证：`{op['auth']}`。\n\n"
        if op["method"] in ["GET","DELETE"]:text+="参数通过路径/查询传入；meta使用X-Request-Id、X-UAW-Schema-Version，DELETE还使用If-Match。不能发送模型上下文或主体字段。\n"
        else:text+="请求体是 `{meta, payload}`；路径ID从path取得，不重复写入payload。OpenAPI记录实际线上字段位置；下方输入对象是服务合成的业务请求。\n"
    elif op["channel"]=="tool":text+=f"LLM提出 `{op['id']}(arguments)` → ToolRuntime校验/权限/必要审批 → `{op['owner']}`负责人。ToolRuntime注入可信上下文，业务参数只使用下方输入结构。\n"
    elif op["channel"]=="runner":text+="配对/本地选择是专用可信交互；执行类消息走 `RunnerCommand` 信封，其中request_ref解析为下方输入。服务签名和本机范围/权限均有效才执行，响应回传ComponentResult，不能把进程启动当成完成。\n"
    else:
        symbol=op['id'].split('.')[-1] if op['channel']=='runtime' else 'handle'
        text+=f"计划Python异步签名：`async def {symbol}(request: {op['request']}, context: TrustedExecutionContext) -> {op['result']}`。所属入口为 `{op['id']}`。该签名是契约目标；实际方法定位见对应开发设计，不能从公网/LLM直接调用私有组件。\n"
    text+="\n## 输入\n\n"+schema_link(op["request"])+"；每个字段的类型、必填性、默认注解、限制和分支见对象页。\n\n"
    if "properties" in inp:
        text+="| 字段 | 类型 | 必填 | 说明 |\n| --- | --- | --- | --- |\n"
        for k,v in inp["properties"].items():text+=f"| `{k}` | {type_label(v)} | {'是' if k in inp.get('required',[]) else '否'} | {v.get('description','见类型').replace('|','／')} |\n"
    else:text+="动作分支：\n\n"+"\n".join("- "+type_label(v) for v in inp.get("oneOf",[]))+"\n"
    text+="\n## 输出\n\n"+schema_link(op["result"])+" 为完整返回结构。`kind=ok` 的payload是 "+schema_link(op["response"])+"。`waiting`带wait_ref，其他非成功状态带Failure，不能用空对象假装成功。\n\n"
    out=TYPES[op["response"]]
    if "properties" in out:
        text+="| payload字段 | 类型 | 必填 | 说明 |\n| --- | --- | --- | --- |\n"
        for k,v in out["properties"].items():text+=f"| `{k}` | {type_label(v)} | {'是' if k in out.get('required',[]) else '否'} | {v.get('description','见类型').replace('|','／')} |\n"
    text+=f"\n## 约束与提交\n\n- 效果分类：`{op['effect']}`。\n- 认证/上下文：`{op['auth']}`；范围及权限由服务端或Runner取得。\n- 请求/动作ID去重与CAS按[统一规则](../CONVENTIONS.md)执行，重复ID不同参数必须冲突。\n"
    if op["feature"]:text+=f"- 功能旗标：`{op['feature']}`；关闭时发现不展示，直接调用/恢复也拒绝。\n"
    text+="\n".join("- "+r for r in op["rules"])+"\n"
    if op["channel"]=="http" and op["method"] not in ["GET","DELETE"] and openapi["paths"][op["path"]][op["method"].lower()].get("x-uaw-cas-required"):
        text+="- HTTP meta.expected_revision必填且≥1；过期提交返回conflict，不能自动覆盖。\n"
    text+="\n## 错误、等待、取消\n\n"+"\n".join("- "+e for e in op["errors"])+"\n\n" if op["errors"] else "\n## 错误、等待、取消\n\n"
    text+="错误对象是 "+schema_link("Failure")+"；统一分类：schema_invalid / permission_denied / feature_disabled / revision_conflict / stale_resource / dependency_unavailable / budget_exceeded / deadline_exceeded / cancelled / unknown_effect。实际Runtime需要把业务错误映射到此对象；上述分类不会代替明确failed_phase和恢复提示。\n\n只读可在有界策略内重试；写失败先核对动作账本，效果unknown时禁止盲重试；waiting通过审批决定、用户输入、process.poll或agents.wait推进。取消只停止后续执行，已有效果如实保留。\n"
    text+="\n## 请求示例\n\n示例展示结构；不代表这些示例引用存在。\n\n"
    sample=EXAMPLES[op["request"]]
    if op["channel"]=="http" and op["method"] not in ["GET","DELETE"]:
        payload=copy.deepcopy(sample)
        for k in re.findall(r"{([^}]+)}",op["path"]):payload.pop(k,None)
        cas=openapi["paths"][op["path"]][op["method"].lower()].get("x-uaw-cas-required",False)
        sample={"meta":{"request_id":"request_001","schema_version":"0.1","expected_revision":3 if cas else 0},"payload":payload}
    text+=fenced(sample)+"\n\n## 成功结构示例\n\n"+fenced({"kind":"ok","payload":EXAMPLES[op["response"]],"output_refs":[]})+"\n"
    text+="\n## 拒绝结构示例\n\n"+fenced({"kind":"denied","output_refs":[],"failure":{"code":"permission_denied","category":"authorization","message":"当前主体没有本动作所需权限。","retryable":False,"failed_phase":"policy_gate","recover_hint":"取得真实授权后重新检查；不能通过换工具绕过。"}})+"\n"
    text+="\n## 模块与目录\n\n| 节点 | 详细策略 | 计划代码位置 |\n| --- | --- | --- |\n"
    for node in op["nodes"]:
        n=node_map[node];design=n["design_doc"]
        text+=f"| `{node}` | [开发设计](../../../{design}) | `{n['code_target']}` |\n"
    text+="\n[接口机器目录](../../../contracts/interfaces.json) · [统一对象schema](../../../contracts/uaw.schema.json)\n"
    write(OUT/"interfaces"/(slug(op)+".md"),text)

write(ROOT/"contracts/interface-map.json",{"version":"0.1","nodes":node_map})

for channel,label in CHANNELS.items():
    text=f"# {label}\n\n[接口总入口](README.md)。状态：设计契约0.1。\n\n| 接口 | 输入 | 成功payload | 效果 |\n| --- | --- | --- | --- |\n"
    for op in OPERATIONS:
        if op["channel"]!=channel:continue
        text+=f"| [{op['id']}](interfaces/{slug(op)}.md) | {schema_link(op['request'],'objects/')} | {schema_link(op['response'],'objects/')} | `{op['effect']}` |\n"
    write(OUT/(channel.upper()+".md"),text)

text="# 对象总字典\n\n[接口总入口](README.md)。所有对象来自同一份[JSON Schema](../../contracts/uaw.schema.json)，包括业务实体、请求DTO、分支对象和每个接口的严格返回结构。生成对象多不等于需要建立相同数量的数据库表或服务。\n\n"
for owner,label in OWNERNAMES.items():
    text+="## "+label+"\n\n| 对象 | 用途 |\n| --- | --- |\n"
    for name in sorted(TYPES):
        if OWNERS[name]==owner:text+=f"| {schema_link(name,'objects/')} | {TYPES[name].get('description','').replace('|','／')} |\n"
write(OUT/"OBJECTS.md",text)

text="# 架构节点与接口覆盖\n\n[接口总入口](README.md)。覆盖表示节点已有契约，不能代替Runtime实现/联调验收。\n\n"
for node,info in node_map.items():
    text+=f"## {node} · {GRAPH['nodes'][node]['label']}\n\n[详细开发设计](../../{info['design_doc']}) · 计划位置：`{info['code_target']}`。\n\n"
    text+="\n".join(f"- [{x['channel']} · {x['id']}](interfaces/{x['channel']}--{x['id'].replace('.','-').replace('_','-')}.md)" for x in info["interfaces"])+"\n\n"
    node_text=f"# {GRAPH['nodes'][node]['label']} · 接口入口\n\n[总覆盖图](../COVERAGE.md) · [详细设计](../../../{info['design_doc']})\n\n计划代码：`{info['code_target']}`。状态：完整节点仍按设计建设，已实现操作见下方接口及实施记录。\n\n"
    if info.get("aggregation_only"):node_text+="这是相关独立设施的汇总入口，不引入第八条Runtime流水线。下面列出各子组件接口。\n\n"
    node_text+="\n".join(f"- [{x['channel']} · {x['id']}](../interfaces/{x['channel']}--{x['id'].replace('.','-').replace('_','-')}.md)" for x in info["interfaces"])+"\n"
    write(OUT/"nodes"/(node+".md"),node_text)
write(OUT/"COVERAGE.md",text)

counts={ch:sum(o["channel"]==ch for o in OPERATIONS) for ch in CHANNELS}
text="# UAW 功能接口总入口\n\n版本：0.1；日期：2026-10-07；对齐架构 "+GRAPH["architecture_version"]+"。**实现范围逐接口记录；开发协议验证不等于产品闭环或生产部署。**\n\n## 从这里开始\n\n1. [统一规则](CONVENTIONS.md)：信任边界、HTTP状态、幂等、CAS、等待/取消、分页/SSE、字段单位。\n2. [关键调用链与实例](FLOWS.md)：创建/调用子Agent、运行代码测试、审批、撤销、完成核验、缓存与恢复。\n3. 按类别找到接口；每页均含入口、字段表、返回结构、约束、错误、示例和代码位置。\n4. [对象总字典](OBJECTS.md)：所有对象、请求、返回和动作分支逐字段定义。\n5. [架构→接口→设计→代码](COVERAGE.md)：核对自己负责模块的契约范围。\n6. [Runner消息协议](RUNNER_PROTOCOL.md)与[早期字段迁移](MIGRATION.md)：执行信封、断线对账和旧schema对齐。\n\n## 五类契约\n\n| 类别 | 条目数 | 访问方式 |\n| --- | --- | --- |\n"
for ch,label in CHANNELS.items():text+=f"| [{label}]({ch.upper()}.md) | {counts[ch]} | {'用户/管理员认证' if ch=='http' else '可信协议/内部调用' if ch in ['runner','runtime','component'] else '仅暴露业务参数给LLM'} |\n"
text+=f"""\n共 {len(OPERATIONS)} 条接口契约，{len(TYPES)} 个命名schema（含自动生成DTO/互斥分支/严格返回类型），覆盖 {len(node_map)} 个当前架构节点。图中的每个小模块是内部组件，不会都变成公网HTTP接口或模型工具。\n\n## 机器文件与维护\n\n| 文件 | 作用 |\n| --- | --- |\n| [uaw.schema.json](../../contracts/uaw.schema.json) | JSON Schema 2020-12统一对象字典 |
| [openapi.json](../../contracts/openapi.json) | OpenAPI 3.1.1 HTTP路径/参数/响应/认证 |
| [tools.json](../../contracts/tools.json) | 模型工具目录与参数/返回schema引用 |
| [interfaces.json](../../contracts/interfaces.json) | 五类接口、Owner、节点、类型、效果及约束 |
| [interface-map.json](../../contracts/interface-map.json) | 节点到接口/策略/代码目录 |
| [examples.json](../../contracts/examples.json) | 结构示例，不是可直接发出的实际请求 |
| [接口检查结果](contract-check.json) | schema/示例/反例/链接与覆盖检查，运行测试另行标记 |
| [interface_catalog.py](../../contracts/interface_catalog.py) | 人工维护对象、操作和约束的唯一契约源 |
| [build_interfaces.py](../../contracts/build_interfaces.py) | 生成机器契约、逐接口和逐对象文档 |
| [check_interfaces.py](../../contracts/check_interfaces.py) | 验证schema、正反示例、引用、链接和节点覆盖 |
\n改变接口先改catalog，再生成和验证；不能只编辑生成Markdown/OpenAPI造成字段漂移。详细算法仍由design/catalog.py负责；schema写字段与硬结构约束，策略文档写处理过程。\n\n## 待确认的产品项\n\n- 历史的权威存储位置仍为云端/本地两个部署选项，契约不替用户决定。\n- assisted/manual/automatic的产品文案需确认；目前按审批专项文档的暂定语义对接。\n- 前端框架、云沙箱提供方与身份登录提供方没有在这些契约中锁定。\n"""
write(OUT/"README.md",text)
print(json.dumps({"interfaces":len(OPERATIONS),"types":len(TYPES),"nodes":len(node_map),"channels":counts},ensure_ascii=False))
