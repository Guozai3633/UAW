"""Build technology documentation and verify planned node/component links only."""
import json
import os
import re
from pathlib import Path

from catalog import BINDINGS, COMPONENTS, INSTALLATION, MODULES

ROOT = Path(__file__).resolve().parents[1]
DATE = "2026-10-07"
GRAPH = json.loads((ROOT / "architecture/graph.json").read_text(encoding="utf-8"))
DESIGN = json.loads((ROOT / "design/design-map.json").read_text(encoding="utf-8"))["nodes"]
API = json.loads((ROOT / "contracts/interface-map.json").read_text(encoding="utf-8"))["nodes"]
PLAN = json.loads((ROOT / "planning/plan-map.json").read_text(encoding="utf-8"))["nodes"]
ROUNDS = {r["id"]: r for r in json.loads((ROOT / "planning/plan.json").read_text(encoding="utf-8"))["rounds"]}
GENERATED = []


def link(path, target, label):
    return f"[{label}]({os.path.relpath(ROOT / target, (ROOT / path).parent).replace(os.sep, '/')})"


def write(path, lines):
    target = ROOT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")
    GENERATED.append(path)


def unique(values):
    return list(dict.fromkeys(values))


def module_doc(id):
    return f"docs/technology/modules/{id}.md"


def node_module(id):
    root = id.split(".")[0]
    return "web" if root == "ui" else "api" if root == "ingress" else root


def nodes_for(id):
    roots = MODULES[id]["roots"]
    return [n for n in GRAPH["nodes"] if n.split(".")[0] in roots]


def source_checks():
    errors = []
    missing = set(GRAPH["nodes"]) - set(BINDINGS)
    extra = set(BINDINGS) - set(GRAPH["nodes"])
    errors += [f"unmapped node: {n}" for n in sorted(missing)]
    errors += [f"unknown node: {n}" for n in sorted(extra)]
    for id, binding in BINDINGS.items():
        for component in binding["components"]:
            if component not in COMPONENTS:
                errors.append(f"unknown node component: {id}->{component}")
        if id in GRAPH["nodes"] and node_module(id) not in MODULES:
            errors.append(f"missing module: {id}")
        for label, mapping in [("design", DESIGN), ("api", API), ("plan", PLAN)]:
            if id not in mapping:
                errors.append(f"missing {label} mapping: {id}")
    for id, module in MODULES.items():
        for component in module["components"]:
            if component not in COMPONENTS:
                errors.append(f"unknown module component: {id}->{component}")
        for r in module["extra_rounds"]:
            if r not in ROUNDS:
                errors.append(f"unknown module round: {id}->{r}")
    return errors


def components_table(ids):
    lines = ["| 组件 | 实际包/服务 | 在本模块承担什么 | 基线与加入时机 |", "| --- | --- | --- | --- |"]
    for id in ids:
        c = COMPONENTS[id]
        name = f"[{c['name']}]({c['source']})" if c["source"] else c["name"]
        lines.append(f"| {name} | `{c['package']}` | {c['role']} | {c['baseline']} / {c['adoption']} |")
    return lines


def module_rounds(id):
    return unique([r for n in nodes_for(id) for r in PLAN[n]["rounds"]] + MODULES[id]["extra_rounds"])


def build_module(id):
    path = module_doc(id)
    m = MODULES[id]
    lines = [f"# {m['name']} · 技术组件设计", "", f"技术v0.1 · {DATE} · 主选设计；实际实施范围见" + link(path, "docs/implementation/README.md", "开发记录") + "。", "",
             link(path, "TECHNOLOGY_STACK.md", "技术总览") + " · " + link(path, "docs/technology/README.md", "模块索引") + " · " + link(path, "docs/technology/FRAMEWORK_BOUNDARIES.md", "框架边界"), "",
             "## 1. 主选组件与使用阶段", "", *components_table(m["components"]), "",
             "表中P4/P5或按需组件不要求首轮全部安装。SDK供应商、账户授权、可选环境和格式仍按产品决策/管理员配置确定；组件主选不会扩大权限。", "",
             "## 2. 接入、细分职责与实现策略", "", m["strategy"], "", "## 3. 架构子节点的具体技术落点", ""]
    if nodes_for(id):
        lines += ["| 节点 | 技术组件 | 如何落地 | 策略 / 准确接口 |", "| --- | --- | --- | --- |"]
        for n in nodes_for(id):
            binding = BINDINGS[n]
            names = "、".join(COMPONENTS[c]["name"] for c in binding["components"])
            refs = link(path, DESIGN[n]["design_doc"], "设计") + " / " + link(path, API[n]["interface_doc"], "接口")
            lines.append(f"| `{n}` | {names} | {binding['implementation']} | {refs} |")
    else:
        lines += ["这是架构边界之外的配套实现分组，按上面的组件分工与相关轮次接入；不创建第八个Runtime或新的任务状态所有者。"]
    lines += ["", "## 4. 目录与依赖位置", "", *[f"- `{p}`" for p in m["paths"]], "",
              "目录为完整开发目标，部分工程设施已实现，业务能力以实际记录为准。领域contracts/ports保留UAW类型；第三方库在实现adapter中使用，composition负责组装。框架或ORM对象不能成为跨Runtime公开协议。", "",
              "## 5. 对应开发轮次与验收", "", "| 工作包 | 本轮职责 | 当前状态 |", "| --- | --- | --- |"]
    for r in sorted(module_rounds(id)):
        entry = ROUNDS[r]
        lines.append(f"| {link(path, entry['document'], r + ' ' + entry['title'])} | {entry['goal']} | {entry['status']} |")
    lines += ["", "关联轮次覆盖主责与协同工作，不等于每轮都实现本模块全部功能。按轮任务/具体能力附真实证据，再核对 " + link(path, "docs/technology/VALIDATION.md", "技术兼容与接入验证") + "。", "",
              "## 6. 本模块接口和对象的权威", "", link(path, "docs/api/OBJECTS.md", "逐字段对象字典") + " · " + link(path, "docs/api/CONVENTIONS.md", "通用约束") + " · " + link(path, "docs/PROJECT_STRUCTURE.md", "目录与依赖"), "",
              "技术表描述实现组件，不新增另一套请求字段。需要签名profile、权限、模型范围等新增字段时先修contracts/策略源，再生成文档和兼容验证。", ""]
    write(path, lines)


def build_index():
    path = "docs/technology/README.md"
    lines = ["# 技术栈与组件文档索引", "", link(path, "TECHNOLOGY_STACK.md", "先看技术总览") + " · " + link(path, "docs/DOCUMENT_MAP.md", "全局文档地图"), "",
             "本轮把主选组件对应到七Runtime及API/Web/Runner/工程等配套模块。每页写组件、细分技术落点、接入/状态/替换策略、目标目录和开发轮，当前仍是技术设计。", "", "## 按模块阅读", "",
             "| 模块 | 对应节点数 | 开发位置 |", "| --- | --- | --- |"]
    for id, module in MODULES.items():
        lines.append(f"| {link(path, module_doc(id), module['name'])} | {len(nodes_for(id))} | {'、'.join('`'+p+'`' for p in module['paths'][:2])} |")
    lines += ["", "Runner/工程/后续适配是配套分组，七Runtime加共享支撑的逻辑边界不变。", "", "## 跨模块设计", "",
              "| 文档 | 回答的问题 |", "| --- | --- |",
              f"| {link(path, 'docs/technology/FRAMEWORK_BOUNDARIES.md', '框架职责')} | LangGraph、LangChain、UAW各自管什么，三个图和父子实例怎样区分 |",
              f"| {link(path, 'docs/technology/DATA_AND_DEPLOYMENT.md', '数据/缓存/部署')} | 唯一权威、事务/待办、向量、缓存和云/本地profile |",
              f"| {link(path, 'docs/technology/DEPENDENCIES.md', '依赖与版本')} | 每个包/服务什么时候加入、怎样冻结、哪些按需 |",
              f"| {link(path, 'docs/technology/VALIDATION.md', '兼容与接入验证')} | 决定框架能否采用、各阶段的真实验证门槛 |",
              f"| {link(path, 'docs/technology/COVERAGE.md', '115节点技术对应表')} | 节点→组件→代码→策略→接口→轮次 |",
              f"| {link(path, 'docs/technology/SOURCES.md', '官方资料')} | 本次查阅的功能/协议资料，库能力与UAW设计分开 |",
              f"| {link(path, 'docs/technology/technology-check.json', '文档检查报告')} | 组件/节点/引用检查；不代表依赖兼容或Runtime通过 |", "",
              "## 维护源与准确性", "", link(path, "technology/catalog.py", "组件/模块/节点主选源") + " · " + link(path, "technology/build_stack.py", "文档与映射生成器") + " · " + link(path, "technology/node-map.json", "机器映射"), "",
              "修改catalog后运行 `python technology/build_stack.py`；框架、数据与验证跨模块文档人工维护。版本采用稳定发行版并在实际开发锁定；官网latest可能展示dev文档，不把该版本直接当安装建议。", "",
              "当前仍待：D01历史权威位置、具体IdP/模型/搜索/embedding/秘密/云执行提供方、首批文件范围、三审批模式最终文案、成本阈值。技术主选已给出，不等同这些产品/部署条件已经确认。", ""]
    write(path, lines)


def build_dependencies():
    path = "docs/technology/DEPENDENCIES.md"
    lines = ["# 组件、依赖分组与版本冻结", "", link(path, "TECHNOLOGY_STACK.md", "技术总览"), "",
             "采用设计主线＋实际兼容锁文件两层。下表是完整主选；P0核心依赖已按uv.lock安装，实际版本/范围见" + link(path, "docs/implementation/evidence/environment.json", "环境回执") + "。其余组件按阶段安装；包存在不等于功能已经可用。", "",
             "## 1. Python依赖组", "", "| 依赖组（计划） | 范围 | 安装时机 |", "| --- | --- | --- |",
             "| runtime-core | FastAPI/Uvicorn、Pydantic/jsonschema、SQLAlchemy/Psycopg/Alembic、HTTPX/structlog | P0/P1最小可用子集 |",
             "| agent-engine | LangGraph及PostgreSQL局部checkpointer/受控serializer | P1-07接线；P1-09审批；P5补复合恢复 |",
             "| providers | 管理员批准的官方SDK；按需LangChain集成 | P0-05及实际新增provider轮 |",
             "| retrieval | pgvector适配/批准embedding adapter | P4-03 |",
             "| formats | pypdf、按需DOCX/XLSX适配 | P2及格式启用轮；解析进程独立 |",
             "| connectors | MCP官方SDK及批准session adapter | P4-05 |",
             "| efficiency/telemetry | cachetools、OpenTelemetry等 | P4/P5，基本日志先启用 |",
             "| runner | 独立Python环境；WS/签名/keyring/psutil/PySide、Windows pywin32 | P1起；不塞入任务项目依赖 |",
             "| development | pytest、pytest-asyncio、Ruff、mypy | P0起，不带入任务执行模板 |", "",
             "后续pyproject中可选依赖组不让代码暗装包；新provider/格式未启用时不会自动变成可发现工具。任务项目依赖单独按锁文件准备。", "",
             "## 2. Web依赖组", "",
             "Node 24 LTS＋pnpm；React/TypeScript/Vite、Tailwind/Radix、Query/Router为页面基础。Monaco、PDF.js等按功能懒加载，worker自托管；openapi-typescript负责生成，Ajv2020负责动态边界。Dexie后置到P4，不把登录令牌写IndexedDB。", "",
             "## 3. 外部服务和系统组件", "",
             "首个数据后端PostgreSQL 17＋私有Blob持久卷。pgvector/pg_trgm在相关轮启用，数据库image/digest与扩展组合一起记录。模型/搜索/IdP/秘密服务是管理员配置的外部依赖，供应商尚未选定。", "",
             "Docker/Compose用于开发编排；本机Git和语言工具探测实际版本。Nginx在正式部署接同源TLS/SSE/WSS。首版不额外要求向量服务、Redis/Celery、Kafka或Kubernetes。", "",
             "## 4. 每个组件的精确职责", "", *components_table(COMPONENTS), "",
             "## 5. 如何冻结与升级", "",
             "1. 主线Python 3.14、Node 24、PG17；确认目标OS与稳定发行包，形成兼容矩阵。",
             "2. 每轮只安装需要的组，验证DTO、状态与真实能力后写uv.lock/pnpm-lock.yaml、实际系统版本和镜像digest。",
             "3. LangGraph/checkpointer/serializer/provider组合一起回归，不能只升级一个包后默认旧检查点可读。",
             "4. 签名算法、JSONprofile、schema/接口和数据库迁移也进入ReleaseManifest，模型/价格/embedding另有配置版本。",
             "5. 发布保留上一可用包、数据迁移/备份步骤、已知限制与能力开关；自动升级不会授予新增工具或网络权限。", "",
             "具体补丁、供应商价格和兼容性需要实施轮再核验，本次不伪造版本锁文件或成本结论。", ""]
    write(path, lines)


def build_coverage(mapping):
    path = "docs/technology/COVERAGE.md"
    lines = ["# 115个架构节点的技术组件落点", "", link(path, "docs/technology/README.md", "技术模块入口"), "",
             "这是技术主选覆盖。自研策略仍按详细设计，字段仍按准确接口；组件已选不代表代码已经写好或依赖已验证。", "", "| 节点 | 技术页 / 组件 | 目标代码 | 策略 / 接口 / 开发轮 |", "| --- | --- | --- | --- |"]
    for n, entry in mapping.items():
        components = "、".join(COMPONENTS[c]["name"] for c in entry["components"])
        refs = link(path, entry["design_doc"], "策略") + " / " + link(path, entry["interface_doc"], "接口") + " / " + "、".join(link(path, ROUNDS[r]["document"], r) for r in entry["rounds"])
        lines.append(f"| `{n}` | {link(path, entry['technology_doc'], MODULES[entry['module']]['name'])}：{components} | `{entry['code_target']}` | {refs} |")
    write(path, lines + ["", "相同组件可被多个模块的adapter使用，但状态所有者不改变。Model SDK只在Model Gateway受控调用，其他模块的语义判断通过该port；本机读写仍通过Workspace/Runner。", ""])


def build_sources():
    path = "docs/technology/SOURCES.md"
    lines = ["# 官方资料与方案依据", "", f"核对日期：{DATE}。技术主选是UAW工程设计，官网资料用于核对库的能力/接口；并不证明UAW的组合已经运行。", "",
             "以下保留官方项目入口。具体SDK供应商/版本、生产配置、许可分发和系统支持在相应实施轮按实际候选继续核对。SDK的main/latest文档可能包含开发版，依赖锁定只使用批准稳定发行版。", "",
             "| 组件 | 官方入口 | UAW使用方向 |", "| --- | --- | --- |"]
    for id, component in COMPONENTS.items():
        if component["source"]:
            lines.append(f"| {component['name']} | [{id}]({component['source']}) | {component['role']} |")
    lines += ["", "## 协议与关键差异", "",
              "- [RFC8785](https://www.rfc-editor.org/rfc/rfc8785)：签名字节规范主选；UAW具体profile需双方测试和契约约束。",
              "- [PostgreSQL SELECT/锁](https://www.postgresql.org/docs/17/sql-select.html)：短claim辅助；长期任务控制由UAW租约/栅栏处理。",
              "- [LangGraph持久化](https://docs.langchain.com/oss/python/langgraph/persistence)：局部图状态；跨领域已提交引用和未知副作用由UAW管理。",
              "- [pgvector](https://github.com/pgvector/pgvector)：近似检索/过滤行为需召回评测；查询范围与工具调用授权仍由UAW检查。", ""]
    write(path, lines)


def check_links(paths):
    count, errors = 0, []
    for path in unique(paths):
        file = ROOT / path
        if not file.is_file() or file.suffix != ".md":
            continue
        for _, dest in re.findall(r"\[([^\]]+)\]\(([^\)]+)\)", file.read_text(encoding="utf-8")):
            if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", dest) or dest.startswith("#"):
                continue
            dest = dest.split("#", 1)[0].strip("<>")
            if dest:
                count += 1
                if not (file.parent / dest).resolve().is_file():
                    errors.append(f"missing link: {path}->{dest}")
    return count, errors


def main():
    errors = source_checks()
    if errors:
        raise SystemExit("\n".join(errors))
    mapping = {n: {**BINDINGS[n], "module": node_module(n), "technology_doc": module_doc(node_module(n)), "design_doc": DESIGN[n]["design_doc"], "interface_doc": API[n]["interface_doc"], "code_target": DESIGN[n]["code_target"], "rounds": PLAN[n]["rounds"], "implemented": False} for n in GRAPH["nodes"]}
    write("technology/node-map.json", [json.dumps({"version": "0.1", "date": DATE, "status": "technology_design_only", "nodes": mapping}, ensure_ascii=False, indent=2)])
    write("technology/components.json", [json.dumps({"version": "0.1", "date": DATE, "dependency_lock": (ROOT / "uv.lock").is_file(), "dependency_lock_scope": "python_core_and_agent_engine_candidate", "components": COMPONENTS, "modules": MODULES}, ensure_ascii=False, indent=2)])
    for id in MODULES:
        build_module(id)
    build_index()
    build_dependencies()
    build_coverage(mapping)
    build_sources()
    report_path = "docs/technology/technology-check.json"
    (ROOT / report_path).write_text("{}\n", encoding="utf-8")
    hand = ["TECHNOLOGY_STACK.md", "docs/technology/FRAMEWORK_BOUNDARIES.md", "docs/technology/DATA_AND_DEPLOYMENT.md", "docs/technology/VALIDATION.md", "README.md", "ARCHITECTURE.md", "docs/DOCUMENT_MAP.md", "docs/PROJECT_STRUCTURE.md", "DEVELOPMENT_PLAN.md", "docs/implementation/README.md", "docs/implementation/P0-01.md", "docs/implementation/P0-02.md", "docs/implementation/DATA_OPERATIONS.md", "docs/decisions/ADR-0001-engineering-bootstrap.md"]
    count, link_errors = check_links(GENERATED + hand)
    errors += link_errors
    report = {"status": "passed" if not errors else "failed", "date": DATE, "module_documents": len(MODULES), "components": len(COMPONENTS), "planned_node_coverage": {"covered": len(mapping), "total": len(GRAPH["nodes"])}, "mapped_rounds": len({r for entry in mapping.values() for r in entry["rounds"]} | {r for module in MODULES.values() for r in module["extra_rounds"]}), "local_document_links_checked": count, "errors": errors, "dependencies_installed": any(c["installed"] for c in COMPONENTS.values()), "installed_components": sum(c["installed"] for c in COMPONENTS.values()), "dependency_compatibility_tested": bool(INSTALLATION.get("compatibility", {}).get("core_checks")), "runtime_behavior_tests_run": bool(INSTALLATION.get("compatibility", {}).get("postgres_development_checks")), "runtime_evidence_scope": INSTALLATION.get("scope", "none"), "runtime_facts_are_imported_from_evidence": True, "limitations": ["this checks authored IDs and existing file links, not runtime/library compatibility", "component versions are design baselines, not resolved installation locks", "planned code paths are not implementation evidence", "external references are documentation sources, not configured provider accounts"]}
    write(report_path, [json.dumps(report, ensure_ascii=False, indent=2)])
    print(json.dumps(report, ensure_ascii=False))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
