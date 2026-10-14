"""Check schema assertions and examples; no claim of running backend tests."""
from pathlib import Path
import argparse,ast,copy,hashlib,json,re,subprocess,sys
import xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser()
parser.add_argument("--dependency-root",help="isolated directory containing jsonschema; not installed by this script")
parser.add_argument("--implementation-source-ref", help="exact 40-hex committed source of preserved implementation evidence; validates history, not current runtime")
args=parser.parse_args()
if args.implementation_source_ref and not re.fullmatch(r"[0-9a-f]{40}", args.implementation_source_ref):
    parser.error("--implementation-source-ref must be an exact immutable commit SHA")
if args.dependency_root:sys.path.insert(0,args.dependency_root)
from jsonschema import Draft202012Validator,FormatChecker
from implementation_catalog import IMPLEMENTATIONS
schema=json.loads((ROOT/"contracts/uaw.schema.json").read_text(encoding="utf-8"));types=schema["$defs"]
catalog=json.loads((ROOT/"contracts/interfaces.json").read_text(encoding="utf-8"))
examples=json.loads((ROOT/"contracts/examples.json").read_text(encoding="utf-8"))["examples"]
openapi=json.loads((ROOT/"contracts/openapi.json").read_text(encoding="utf-8"))
graph=json.loads((ROOT/"architecture/graph.json").read_text(encoding="utf-8"))
mapping=json.loads((ROOT/"contracts/interface-map.json").read_text(encoding="utf-8"))
errors=[];negative=[]
current_source_differences=[]
Draft202012Validator.check_schema(schema)

# Implementation flags are reviewed declarations, checked against source and existing test
# evidence here. This checker itself never executes the runtime or proves product completeness.
def implementation_evidence():
    counts={key:0 for key in ("tests","failures","errors","skipped")}
    try:
        path=ROOT/"docs/implementation/evidence/p0-tests.xml"
        for suite in ET.parse(path).getroot().iter("testsuite"):
            for key in counts:counts[key]+=int(suite.get(key,"0"))
        if not counts["tests"] or any(counts[k] for k in ("failures","errors","skipped")):
            errors.append({"kind":"implementation_tests_not_passing","counts":counts})
        environment=json.loads((ROOT/"docs/implementation/evidence/environment.json").read_text(encoding="utf-8"))
        if environment["test_counts"]!=counts or environment["test_evidence_sha256"]!=hashlib.sha256(path.read_bytes()).hexdigest():
            errors.append({"kind":"implementation_test_evidence_stale"})
        hashes=environment["source_hashes"]
        snapshot={}
        if args.implementation_source_ref:
            paths=list(hashes)
            result=subprocess.run(["git","cat-file","--batch"],cwd=ROOT,check=True,capture_output=True,
                input="".join(args.implementation_source_ref+":"+p+"\n" for p in paths).encode()).stdout
            position=0
            for source in paths:
                end=result.index(b"\n",position)
                parts=result[position:end].split()
                if parts[-1]==b"missing":
                    raise ValueError("missing source in implementation snapshot")
                size=int(parts[-1]);snapshot[source]=result[end+1:end+1+size]
                position=end+1+size+1
        for source,digest in hashes.items():
            target=(ROOT/source).resolve()
            if not target.is_relative_to(ROOT) or not target.is_file():
                errors.append({"kind":"implementation_source_evidence_stale","source":source})
                continue
            current=target.read_bytes()
            actual=snapshot.get(source,current)
            if hashlib.sha256(actual).hexdigest()!=digest:
                errors.append({"kind":"implementation_source_evidence_stale","source":source})
            if hashlib.sha256(current).hexdigest()!=digest:
                current_source_differences.append(source)
        for item in IMPLEMENTATIONS.values():
            if item["entrypoint"] not in hashes:
                errors.append({"kind":"implementation_entrypoint_without_source_hash","source":item["entrypoint"]})
        # Read the literal route table without importing startup/configuration code.
        tree=ast.parse((ROOT/"src/uaw/api/routes.py").read_text(encoding="utf-8"))
        table=next(ast.literal_eval(node.value) for node in tree.body if isinstance(node,ast.Assign)
                   and any(isinstance(target,ast.Name) and target.id=="ROUTES" for target in node.targets))
        actual={row[0]:row[1:] for row in table}
        declared={op["id"]:(op["method"],op["path"],op["request"],op["response"])
                  for op in catalog["operations"] if op["channel"]=="http" and op["implemented"]}
        if actual!=declared:errors.append({"kind":"implemented_http_routes_drift"})
    except (OSError,ValueError,KeyError,StopIteration,ET.ParseError,subprocess.CalledProcessError):
        errors.append({"kind":"implementation_evidence_missing_or_invalid"})
    return counts

implementation_test_counts=implementation_evidence()
def validator(name):return Draft202012Validator({"$schema":schema["$schema"],"$defs":types,"$ref":"#/$defs/"+name},format_checker=FormatChecker())
def references(value):
    if isinstance(value,dict):
        if "$ref" in value:yield value["$ref"]
        for v in value.values():yield from references(v)
    elif isinstance(value,list):
        for v in value:yield from references(v)
for ref in references(schema):
    if not ref.startswith("#/$defs/") or ref[8:] not in types:errors.append({"kind":"unresolved_schema_ref","ref":ref})
for name,data in examples.items():
    issues=list(validator(name).iter_errors(data))
    if issues:errors.append({"kind":"positive_example","name":name,"errors":[{"path":"/"+"/".join(str(x) for x in e.absolute_path),"reason":e.message[:500]} for e in issues[:3]]})
def reject(name,data,label):
    passed=not validator(name).is_valid(data);negative.append({"case":label,"schema":name,"rejected":passed})
    if not passed:errors.append({"kind":"negative_example_accepted","case":label})
base=copy.deepcopy(examples["ToolAgentsCreateInput"])
for forbidden in ["owner_id","conversation_id","approved","trusted_context"]:
    reject("ToolAgentsCreateInput",dict(base,**{forbidden:"spoofed"}),"agent create rejects "+forbidden)
reject("ModelRequest",{"mode":"explicit","requested_name":"unregistered_model"},"explicit requires user source")
reject("ModelRequest",{"mode":"inherit","requested_name":"silently_changed"},"inherit cannot silently request replacement")
reject("ModelRequest",{"mode":"auto"},"auto requires authorization source")
reject("ConversationModelChoice",{"mode":"auto","allowed_model_ids":[]},"auto cannot use empty model universe")
reject("ConversationModelChoice",{"mode":"inherit"},"conversation cannot inherit nonexistent parent")
for path in ["../secret","C:\\secret.txt","/etc/passwd","src/../../secret","\\server\\share"]:
    reject("RelativePath",path,"reject lexical path escape "+path)
reject("Budget",dict(examples["Budget"],limits=dict(examples["Budget"]["limits"],money=-1)),"money cannot be numeric/negative")
reject("ProcessSpec",dict(examples["ProcessSpec"],timeout_ms=0),"process timeout must be positive")
reject("ProcessSpec",dict(examples["ProcessSpec"],shell_command="go test ./..."),"shell requires approved shell profile")
base=copy.deepcopy(examples["ToolFileWriteInput"]);base.pop("expected_content_hash")
reject("ToolFileWriteInput",base,"existing file write requires content hash")
reject("ToolFileWriteInput",dict(examples["ToolFileWriteInput"],content_ref=examples["Ref"]),"text/blob write mutually exclusive")
reject("ReviewDecision",dict(examples["ReviewDecision"],decision="partial_accept",selected_unit_ids=[]),"partial accept requires selection")
reject("ApprovalDecision",dict(examples["ApprovalDecision"],decision="approve_scoped"),"scope approval requires scope and expiry")
reject("ItemPatch",dict(examples["ItemPatch"],text_delta="delta",replacement_text="replace"),"cannot mix text delta and replacement")
reject("RequirementVerdict",dict(examples["RequirementVerdict"],state="passed",evidence_refs=[]),"passing requirement needs evidence")
base=copy.deepcopy(examples["VerificationCheck"]);base.pop("process_ref",None)
reject("VerificationCheck",base,"passing command check needs actual process reference")
reject("DeliveryProposal",dict(examples["DeliveryProposal"],outcome="succeeded",unresolved_effect_refs=[examples["Ref"]]),"unknown external effect cannot claim full success")
reject("ToolResult",dict(examples["ToolResult"],status="succeeded",effect_state="unknown"),"tool success requires confirmed effect")
reject("AccountConnectionView",dict(examples["AccountConnectionView"],credential_ref=examples["Ref"]),"user connection view excludes credential handle")
reject("RequestMeta",dict(examples["RequestMeta"],schema_version="unsupported_9"),"reject unsupported contract version")
reject("ModelOutput",dict(examples["ModelOutput"],text_complete=False),"large model preview requires full content reference")
reject("UserInputRef",dict(examples["Ref"],kind="web"),"web content cannot be user authorization source")
reject("ConversationRequestMeta",dict(examples["ConversationRequestMeta"],schema_version="0.1"),"conversation controls cannot use legacy meta")
reject("ConversationRequestMeta",dict(examples["ConversationRequestMeta"],expected_revision=0),"continuation requires positive original Run CAS")
reject("FirstDecision",dict(examples["FirstReplyDecision"],calls=[]),"reply cannot mix a tool branch")
reject("FirstDecision",dict(examples["FirstReplyDecision"],approved=True),"first decision cannot create runtime approval")
reject("ReplyProposal",dict(examples["ReplyProposal"],unresolved_effect_refs=[examples["Ref"]]),"message completion cannot omit unknown effect reconciliation")
reject("RunClarificationAnswerRequest",dict(examples["RunClarificationAnswerRequest"],text=" ",attachment_refs=[]),"empty clarification answer is not an input")
reject("ClarificationQuestion",dict(examples["ClarificationQuestion"],state="answered"),"answered question requires actual input source")
reject("RunExecutionClock",dict(examples["RunExecutionClock"],mode="waiting_for_user"),"pause requires original waiting item and cannot retain an active segment")
base=copy.deepcopy(examples["ExecutionAssessment"]);base.update(parallelism="serial",parallel_scope="agents")
reject("ExecutionAssessment",base,"serial assessment cannot request agent parallelism")
base=copy.deepcopy(examples["ExecutionAssessment"]);base.update(delegation="single",parallel_scope="agents")
reject("ExecutionAssessment",base,"single agent can parallelize tools but cannot claim agent parallelism")
for op in catalog["operations"]:
    reject(op["result"],{"kind":"ok","output_refs":[]},op["channel"]+":"+op["id"]+" cannot succeed without payload")
    if op["request"] not in types or op["response"] not in types:errors.append({"kind":"operation_type_missing","id":op["id"]})
    if not op["nodes"]:errors.append({"kind":"operation_without_owner_node","id":op["id"]})
    for node in op["nodes"]:
        if node not in graph["nodes"]:errors.append({"kind":"unknown_node","node":node})
    expected=IMPLEMENTATIONS.get(op["id"])
    if bool(expected)!=op["implemented"] or (expected and op.get("implementation")!=expected):
        errors.append({"kind":"implementation_manifest_drift","id":op["id"]})
    if expected:
        for source in [expected["entrypoint"],*expected["evidence"]]:
            target=(ROOT/source).resolve()
            if not target.is_relative_to(ROOT) or not target.is_file():
                errors.append({"kind":"implementation_evidence_path_missing","id":op["id"],"source":source})
ids=[]
for path,methods in openapi["paths"].items():
    for method,operation in methods.items():
        ids.append(operation["operationId"])
        expected=set(re.findall(r"{([^}]+)}",path))
        actual={p["name"] for p in operation["parameters"] if p["in"]=="path" and p.get("required")}
        if expected!=actual:errors.append({"kind":"openapi_path_parameters","path":path})
        if method in ["post","patch","put"]:
            body=operation["requestBody"]["content"]["application/json"]["schema"]
            req=next(o["request"] for o in catalog["operations"] if o["channel"]=="http" and o["path"]==path and o["method"].lower()==method)
            op=next(o for o in catalog["operations"] if o["channel"]=="http" and o["path"]==path and o["method"].lower()==method)
            sample={"meta":{"request_id":"request_001","schema_version":op.get("wire_version", "0.1"),"expected_revision":3},"payload":copy.deepcopy(examples[req])}
            for key in expected:sample["payload"].pop(key,None)
            test=Draft202012Validator({"components":openapi["components"],"allOf":[body]},format_checker=FormatChecker())
            if not test.is_valid(sample):errors.append({"kind":"openapi_wire_example","path":path})
if len(ids)!=len(set(ids)):errors.append({"kind":"duplicate_operationId"})
for ref in references(openapi):
    if not ref.startswith("#/components/schemas/") or ref.split("/")[-1] not in openapi["components"]["schemas"]:errors.append({"kind":"openapi_unresolved_ref","ref":ref})
covered={k for k,v in mapping["nodes"].items() if v["interfaces"]};missing=set(graph["nodes"])-covered
if missing:errors.append({"kind":"node_coverage","missing":sorted(missing)})
links=0
for file in (ROOT/"docs/api").rglob("*.md"):
    for link in re.findall(r"\]\(([^)]+)\)",file.read_text(encoding="utf-8")):
        if link.startswith(("http:","https:","#")):continue
        target=link.split("#",1)[0]
        if not target:continue
        links+=1
        if not (file.parent/target).resolve().exists():errors.append({"kind":"broken_link","file":str(file.relative_to(ROOT)),"target":link})
report={"date":"2026-10-14","contract_version":catalog["contract_version"],"schema_validator":"jsonschema Draft202012Validator with FormatChecker","schema_meta_validation":"passed","named_schemas":len(types),"positive_examples":len(examples),"negative_cases":len(negative),"negative_rejections":sum(x["rejected"] for x in negative),"interfaces":len(catalog["operations"]),"nodes_covered":len(covered),"nodes_total":len(graph["nodes"]),"openapi_checks":"structural_refs_parameters_wire_examples_only_not_full_OpenAPI_meta_validation","local_links_checked":links,"errors":errors,"runtime_integration_tests":"not_executed_by_contract_checker_see_implementation_evidence","semantic_authorization_version_effect_checks":"not_executed_by_contract_checker"}
report["reviewed_implementation_evidence"]={"operations":len(IMPLEMENTATIONS),"existing_test_counts":implementation_test_counts,"source_snapshot_ref":args.implementation_source_ref,"current_source_differences":current_source_differences,"checks":"manifest, literal HTTP route table, preserved test hashes and exact source snapshot; not current full-runtime verification"}
(ROOT/"docs/api/contract-check.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
(ROOT/"contracts/negative-examples.json").write_text(json.dumps({"cases":negative},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps({k:(v[:8] if k=="errors" else v) for k,v in report.items()},ensure_ascii=False,indent=2))
if errors:sys.exit(1)
