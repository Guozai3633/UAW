"""Generate development work packages and check their document/dependency links.

This builds a plan, not the UAW runtime. Authored tasks live in catalog.py.
"""
import json
import os
import re
from collections import Counter
from pathlib import Path

from catalog import DECISIONS, MODULES, PHASES, ROUNDS
from parallel_catalog import PACKAGES

ROOT = Path(__file__).resolve().parents[1]
DATE = "2026-10-07"
GRAPH = json.loads((ROOT / "architecture/graph.json").read_text(encoding="utf-8"))
NODES = GRAPH["nodes"]
DESIGNS = json.loads((ROOT / "design/design-map.json").read_text(encoding="utf-8"))["nodes"]
INTERFACES = json.loads((ROOT / "contracts/interface-map.json").read_text(encoding="utf-8"))["nodes"]
OPERATIONS = json.loads((ROOT / "contracts/interfaces.json").read_text(encoding="utf-8"))["operations"]
ROUND_BY_ID = {r["id"]: r for r in ROUNDS}
DECISION_BY_ID = {d["id"]: d for d in DECISIONS}
PHASE_GATES = {"P0": "P0-05", "P1": "P1-11", "P2": "P2-09", "P3": "P3-08", "P4": "P4-10", "P5": "P5-07"}
STATUS_LABELS = {"planned": "待开发", "deferred": "后续讨论", "in_progress": "开发中", "blocked": "存在具体阻碍", "accepted": "已验收"}
SCOPE_LABELS = {"required": "核心开发范围", "target_implementation_default_disabled": "目标：实现后默认关闭；不挡首次试用", "future_adapter_design_only": "后续适配设计；本次不排实现"}
CHANNELS = {"http": "HTTP", "tool": "模型工具", "runner": "Runner", "runtime": "Runtime公共入口", "component": "内部组件"}
GENERATED = []


def unique(values):
    return list(dict.fromkeys(values))


def link(from_path, to_path, label):
    relative = os.path.relpath(ROOT / to_path, (ROOT / from_path).parent).replace(os.sep, "/")
    return f"[{label}]({relative})"


def write(path, lines):
    target = ROOT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")
    GENERATED.append(path)


def write_json(path, value):
    write(path, [json.dumps(value, ensure_ascii=False, indent=2)])


def round_path(id):
    return f"docs/plan/rounds/{id}.md"


def round_link(path, id, title=False):
    r = ROUND_BY_ID[id]
    return link(path, round_path(id), f"{id} {r['title']}" if title else id)


def phase_rounds(phase):
    return [r for r in ROUNDS if r["phase"] == phase]


def related_modules(r):
    return unique([r["module"]] + ["product" if n.split(".")[0] in ("ui", "ingress") else n.split(".")[0] for n in r["nodes"]])


def module_rounds(module):
    return [r for r in ROUNDS if module in related_modules(r)]


def code_target(node):
    value = DESIGNS[node]["code_target"]
    # UI target is a planned directory; the design map appends an explanation.
    return value.split("（", 1)[0].rstrip("/") + "/" if "（" in value else value


def effective_dependencies(r):
    deps = list(r["depends_on"])
    index = list(PHASES).index(r["phase"])
    if index:
        deps.append(PHASE_GATES[list(PHASES)[index - 1]])
    return unique(deps)


def related_operations(r):
    nodes = set(r["nodes"])
    return [o for o in OPERATIONS if nodes.intersection(o["nodes"])]


def round_record(r):
    return {
        **r,
        "effective_dependencies": effective_dependencies(r),
        "document": round_path(r["id"]),
        "related_module_groups": related_modules(r),
        "design_documents": unique(DESIGNS[n]["design_doc"] for n in r["nodes"]),
        "interface_documents": unique(INTERFACES[n]["interface_doc"] for n in r["nodes"]),
        "interface_associations": [{"channel": o["channel"], "id": o["id"], "request": o["request"], "response": o["response"]} for o in related_operations(r)],
        "planned_code_targets": unique([code_target(n) for n in r["nodes"]] + r["extra_code_dirs"]),
        "implementation_record_target": f"docs/implementation/{r['id']}.md",
        "parallel_packages": [p["id"] for p in PACKAGES if r["id"] in p["rounds"]],
    }


def table_rounds(path, rounds, module=None):
    lines = ["| 轮次与任务 | 目标 | 直接前置 | 范围/当前状态 |", "| --- | --- | --- | --- |"]
    for r in rounds:
        deps = "、".join(round_link(path, d) for d in r["depends_on"]) or "无"
        role = ("本组主责；" if r["module"] == module else "跨模块协同；") if module else ""
        lines.append(f"| {round_link(path, r['id'], True)} | {r['goal']} | {deps} | {role}{SCOPE_LABELS[r['scope']]} / {STATUS_LABELS[r['status']]} |")
    return lines


def build_round(r):
    path = round_path(r["id"])
    phase = PHASES[r["phase"]]
    records = round_record(r)
    nav = " · ".join([link(path, "docs/plan/README.md", "计划总索引"), link(path, f"docs/plan/modules/{r['module']}.md", MODULES[r["module"]][0]), link(path, "docs/plan/SEQUENCE.md", "全局实施顺序")])
    lines = [f"# {r['id']} · {r['title']}", "", nav, "",
             f"阶段：{r['phase']} {phase['name']} · 当前状态：**{STATUS_LABELS[r['status']]}** · 范围：{SCOPE_LABELS[r['scope']]}。", "",
             "工作包的计划与实际验收报告分开。每轮不固定对应一天、一次聊天或一个提交；超出可验收范围时拆分子轮，保留依赖和验收条件。", "",
             "主责：" + MODULES[r["module"]][0] + "；关联模块：" + "、".join(link(path, f"docs/plan/modules/{m}.md", MODULES[m][0]) for m in related_modules(r)) + "。", "",
             "## 1. 本轮目标", "", r["goal"], "", "## 2. 开始条件与依赖", ""]
    lines += [f"- 前置工作包：{round_link(path, d, True)}。" for d in r["depends_on"]] or ["- 无前置实现轮；先核对当前产品约束和接口契约。"]
    phase_index = list(PHASES).index(r["phase"])
    if phase_index:
        gate = PHASE_GATES[list(PHASES)[phase_index - 1]]
        lines += [f"- 整轮联调/正式验收门槛：{round_link(path, gate, True)} 已验收。独立组件可按并行子包提前开发，不能因此跳过正式门槛。"]
    parallel = [p for p in PACKAGES if r["id"] in p["rounds"]]
    if parallel:
        lines += ["- 多session子包：" + "、".join(f"{p['id']}（Session {p['session']}）" for p in parallel) + "；开始条件与允许修改路径见" + link(path, "docs/plan/PARALLEL.md", "并行开发计划") + "，不是整轮无依赖声明。"]
    lines += ["- 在开发记录中列出实际负责人、代码基线、可用提供方/设备、场景初态和验收方式。"]
    for decision in r["decision_dependencies"]:
        d = DECISION_BY_ID[decision]
        lines += [f"- 决策 `{decision}`：{d['question']} {d['fallback']}"]
    lines += ["", link(path, "docs/plan/DECISIONS.md", "查看全部待定项与最晚决策轮"), "", "## 3. 每项开发任务", ""]
    lines += [f"{i}. {task}" for i, task in enumerate(r["tasks"], 1)]
    lines += ["", "## 4. 设计、接口、对象与代码位置", ""]
    if r["nodes"]:
        lines += ["| 架构节点 | 详细处理策略 | 输入/输出/约束入口 | 计划代码位置 |", "| --- | --- | --- | --- |"]
        for n in r["nodes"]:
            lines.append(f"| `{n}` · {NODES[n]['label']} | {link(path, DESIGNS[n]['design_doc'], '详细设计')} | {link(path, INTERFACES[n]['interface_doc'], '本节点接口')} | `{code_target(n)}` |")
    else:
        lines += ["这是跨模块验收或后续适配工作包，按前置轮的代码与证据联测；不新增Runtime。", "", link(path, "docs/design/README.md", "全部节点设计") + " · " + link(path, "docs/api/README.md", "全部接口")]
    if r["extra_code_dirs"]:
        lines += ["", "其他本轮目标目录：", "", *[f"- `{directory}`" for directory in r["extra_code_dirs"]]]
    related = related_operations(r)
    if related:
        counts = Counter(o["channel"] for o in related)
        lines += ["", "接口关联：" + "、".join(f"{CHANNELS[k]} {v}项" for k, v in counts.items()) + "。", "",
                  "这些是节点关联范围，**不是本轮必须一次实现的所有端点**。大模块入口会汇总后续能力；只在本轮任务边界内落地DTO、调用和错误分支，未实现分支保持不可用。精确关联ID/请求/返回见机器计划，每个接口也可从上表进入。"]
    lines += ["", link(path, "docs/api/OBJECTS.md", "逐字段对象字典") + " · " + link(path, "contracts/uaw.schema.json", "统一schema") + " · " + link(path, "docs/api/CONVENTIONS.md", "通用约束"), "",
              link(path, "TECHNOLOGY_STACK.md", "本轮技术主选总览") + " · " + link(path, "docs/technology/VALIDATION.md", "实际兼容与接入验证门槛"), "",
              "字段以契约源为准，算法以详细设计为准。发现RoleProfile、模型授权或动作分支缺字段时先更新契约和策略，再生成文档；不能在工具参数中私加字段。计划代码路径表示待建设位置，不表示文件已存在。", "",
              "## 5. 交付物", ""]
    lines += [f"- {value}。" for value in r["deliverables"]]
    if r["scope"] != "future_adapter_design_only":
        if r["module"] == "foundation" and not r["nodes"]:
            lines += ["- 跨模块真实验收记录、可重复演示方式和失败场景回执；实现修改回到各责任模块。"]
        else:
            lines += ["- 本轮真实实现、可重复执行方式，以及本轮确有必要的验证用例/实际场景回执。"]
    report_exists = (ROOT / records['implementation_record_target']).is_file()
    lines += [f"- 开发记录目标：`{records['implementation_record_target']}`，记录实际命令/回执/代码基线、结果和未过项。" + ("已有实施记录，见下方证据。" if report_exists else "当前尚未创建这份实现报告。"), "", "## 6. 验收条件与必要验证", ""]
    lines += [f"- [{'x' if r['status'] == 'accepted' else ' '}] {value}" for value in r["acceptance"]]
    if r["scope"] == "future_adapter_design_only":
        lines += ["", "本轮仅审阅适配设计；不据此声明推特入口可运行，也不加入独立UAW核心试用门槛。"]
    else:
        lines += ["", "状态/版本/权限规则可用受控fixture验证；凡本轮声称真实模型、工具、文件、进程、联网或环境已经可用，必须保留实际回执。Mock、接口示例和HTML演示不能替代真实连通或阶段场景验收。", "",
                  "语义质量按原始需求、材料和证据审阅，不以字数/固定关键词替代；工具退出0也不自动证明整个用户任务完成。只加与本轮风险有关的检查，不追求测试数量。"]
    lines += ["", "## 7. 退出、失败与下一步", "",
              "- 所列验收通过、实际证据可查、未实现能力可见且没有破坏前一阶段场景，才能提交本轮验收。",
              "- 缺模型、设备、批准后端或明确范围时记录具体阻碍；可继续独立任务，但对应真实验收不能标通过。",
              "- 发现跨模块问题回到状态所有者修复；不能靠隐藏失败、重写原文、扩大权限或静默换模型绕过。"]
    followers = [x["id"] for x in ROUNDS if r["id"] in x["depends_on"]]
    lines += ["", "直接后续：" + ("、".join(round_link(path, id, True) for id in followers) if followers else "在阶段验收/交付盘点中汇总；详见全局顺序。"), "", "## 8. 当前进度记录", "",
              f"- 状态：{STATUS_LABELS[r['status']]}。",
              "- 负责人/实际开始/实际完成：见实施记录；尚未实施时待填。",
              "- 实现证据：" + ("、".join(link(path, ref, ref) for ref in r["implementation_evidence"]) if r["implementation_evidence"] else "目前为空") + "；本文编写和链接检查不计入Runtime实现进度。",
              "- 实施时使用 " + link(path, "docs/plan/ROUND_TEMPLATE.md", "每轮记录模板") + "，将计划与实际报告分开保存。", ""]
    write(path, lines)


def build_module(id):
    path = f"docs/plan/modules/{id}.md"
    name, description = MODULES[id]
    rounds = module_rounds(id)
    primary_count = sum(r["module"] == id for r in rounds)
    dirs = unique(target for r in rounds for target in round_record(r)["planned_code_targets"])
    lines = [f"# {name} · 开发计划", "", link(path, "docs/plan/README.md", "计划总索引") + " · " + link(path, "docs/plan/SEQUENCE.md", "全局顺序与并行条件"), "", "## 职责与边界", "", description, "",
             f"本分组主责{primary_count}轮，另关联{len(rounds)-primary_count}轮跨模块协同。按阶段逐步完善，并与其他模块轮次交替接线；协同任务引用同一个工作包，不重复计算50轮总数。七Runtime是运行职责，11个计划分组包含工程、页面和后续适配，不是11个服务。", "", "## 阶段与工作包", ""]
    for phase, info in PHASES.items():
        group = [r for r in rounds if r["phase"] == phase]
        if group:
            lines += [f"### {phase} · {info['name']}", "", *table_rounds(path, group, id), ""]
    lines += ["## 设计与接口入口", "", "| 节点 | 详细设计 | 接口与对象入口 |", "| --- | --- | --- |"]
    for n in unique(n for r in rounds for n in r["nodes"]):
        lines.append(f"| `{n}` | {link(path, DESIGNS[n]['design_doc'], NODES[n]['label'])} | {link(path, INTERFACES[n]['interface_doc'], '逐接口定义')} |")
    if not any(r["nodes"] for r in rounds):
        lines += ["| 后续入口 | 范围待确定，不增通用业务Runtime | 复用现有受理/控制/成果协议 |"]
    lines += ["", "## 目标代码/验证目录", "", *[f"- `{d}`" for d in dirs], "",
              "目录均为开发目标。每轮新增文件保持所属facade/port边界；共享设施分组不成为处理所有请求的统一业务Runtime。", "", "## 本模块验收怎样汇总", "",
              "按本页各轮验收与对应阶段真实场景确认。一个根节点关联到多轮，早期有最小实现不表示其记忆、并行、恢复等后续分支已完成；各能力要分别附代码/回执/版本。", ""]
    write(path, lines)


def build_readme():
    path = "docs/plan/README.md"
    core = sum(r["scope"] == "required" for r in ROUNDS)
    lines = ["# UAW 开发计划总索引", "", f"计划v0.1 · {DATE} · 对齐架构{GRAPH['architecture_version']}。当前仅有设计/接口/蓝图，Runtime实现尚未开始。", "",
             f"按 **模块 → 阶段 → 每轮任务** 组织，共{len(MODULES)}个职责分组、{len(PHASES)}个阶段、{len(ROUNDS)}轮：{core}轮核心开发与验收，1轮实现后默认关闭的扩展，1轮后续推特适配设计。", "",
             "每轮都有目标、前置依赖、待定项、逐项任务、详细设计/接口/对象入口、目标代码目录、交付物和验收条件。轮次是可验收工作包；工期、负责人和每轮大小根据实际团队填写，不虚构完成日期。", "",
             "## 1. 先按职责找到自己的模块", "", "| 模块分组 | 主责轮数 | 负责什么 |", "| --- | --- | --- |"]
    for id, (name, description) in MODULES.items():
        count = sum(r["module"] == id for r in ROUNDS)
        lines.append(f"| {link(path, f'docs/plan/modules/{id}.md', name)} | {count} | {description} |")
    lines += ["", "模块页也列出该模块参与的协同轮，例如Intent预览在页面轮接线、工作区测试在完成验收轮核对；这些都链接到同一份轮文档，不重复计数。", "", "## 2. 再看所在阶段与每轮", "", "| 阶段 | 目标 | 轮数 | 核心门槛轮 |", "| --- | --- | --- | --- |"]
    for id, phase in PHASES.items():
        lines.append(f"| {id} · {phase['name']} | {phase['goal']} | {len(phase_rounds(id))} | {round_link(path, PHASE_GATES[id])} |")
    lines += ["", link(path, "docs/plan/STAGES.md", "阶段门槛与真实样例") + " · " + link(path, "docs/plan/SEQUENCE.md", "50轮全局实施顺序与依赖") + " · " + link(path, "docs/plan/STATUS.md", "当前状态"), "",
              "先贯通单Agent真实任务；再增加角色/单子任务、办公/学术；随后按真实收益补规划、并行、缓存和恢复。开完整模块接口并不意味着请求每次必经全部模块，也不要求先实现全部设计schema。", "",
              "## 3. 配套入口", "", "| 文档 | 用途 |", "| --- | --- |",
              f"| {link(path, 'docs/plan/DECISIONS.md', '待定项与决策轮次')} | 历史权威、提供方、审批与首批格式的待定项，以及技术组合的兼容门槛 |",
              f"| {link(path, 'docs/plan/COVERAGE.md', '节点开发覆盖')} | 115节点→实施轮→策略/接口/代码位置；覆盖不等于已实现 |",
              f"| {link(path, 'docs/plan/INTERFACE_ASSIGNMENTS.md', '接口关联工作包')} | {len(OPERATIONS)}接口→相关轮次；精确字段复用接口字典 |",
              f"| {link(path, 'docs/plan/ROUND_TEMPLATE.md', '每轮执行记录模板')} | 从计划开始到真实验收如何记录 |",
              f"| {link(path, 'docs/plan/PARALLEL.md', '多session分工')} | 3个开发＋1个集成；子包、目录归属与依赖 |",
              f"| {link(path, 'docs/plan/PARALLEL_WORKFLOW.md', '并行开工和合并流程')} | 共同基线、worktree、接口提案、交接和回归 |",
              f"| {link(path, 'docs/PROJECT_STRUCTURE.md', '项目目录设计')} | 代码目录/依赖方向 |",
              f"| {link(path, 'planning/catalog.py', '计划维护源')} | 手写任务、门槛、依赖、范围 |",
              f"| {link(path, 'planning/plan.json', '机器可读计划')} | 消费全部任务与输入/输出接口关联 |",
              f"| {link(path, 'planning/plan-map.json', '节点到轮次映射')} | 反查节点由哪些轮逐步实现 |",
              f"| {link(path, 'docs/plan/plan-check.json', '计划检查结果')} | 依赖无环、节点/接口关联、文档链接检查；不是Runtime测试 |", "",
              "## 4. 当前接续入口", "", "P0工程/受理基础已经实施；真实模型仍待配置。" + round_link(path, "P1-01", True) + "协议、三份组件及MS-I1接线已通过222项全量检查，语义质量仍待实际模型验证。B按ms-i1基线执行MS-C2，A继续Tool/Runner公共接线；见" + link(path, "docs/plan/PARALLEL.md", "多session分工") + "，完整轮验收仍遵守原依赖。", "",
              "## 5. 计划维护规则", "",
              "- 修改planning/catalog.py后运行 `python planning/build_plan.py`；逐轮/模块/阶段/映射是生成文件。",
              "- 开发报告保存在 `docs/implementation/<轮次>.md`，实际选型保存在 `docs/decisions/`，实施时才创建。",
              "- 只有验收证据齐全才能将轮次改为accepted；flag关闭、目录存在或schema检查通过不能当成功。",
              "- 待定项不需要阻止独立前置工作；依赖它的真实场景验收必须先确定它。",
              "- 核心试用门槛不依赖P5-04/P5-06；完整扩展目标另跟踪P5-04，推特范围确认后再排实现。", ""]
    write(path, lines)


def build_stages():
    path = "docs/plan/STAGES.md"
    lines = ["# 阶段目标、门槛与能力开关", "", link(path, "docs/plan/README.md", "计划总索引"), "",
             "这是开发交付顺序，运行时仍由当前LLM按任务选择所需能力。阶段之间以真实验收作为门槛；在前阶段未过时可以准备后阶段资料/隔离原型，但不能把后阶段标为已交付。", "",
             "```mermaid", "flowchart LR", '  P0["P0 工程与固定模型"] --> P1["P1 单Agent真实闭环"]', '  P1 --> P2["P2 角色与三类成果"]', '  P2 --> P3["P3 规划与并行"]', '  P3 --> P4["P4 效率与能力治理"]', '  P4 --> P5["P5 恢复与受控试用"]', "```", ""]
    for id, phase in PHASES.items():
        lines += [f"## {id} · {phase['name']}", "", f"**目标：**{phase['goal']}", "", f"**真实样例：**{phase['sample']}", "", f"**退出门槛：**{phase['gate']}", "", f"**门槛工作包：**{round_link(path, PHASE_GATES[id], True)}。", "", *table_rounds(path, phase_rounds(id)), ""]
    lines += ["## 每阶段都能交出可检查的版本", "",
              "P1先交付本机开发演示；P2交付三类样例和会话角色的小范围体验版本，并开始收集接受/返工/成本记录；P3/P4逐步增加能力。它们不必等P5才让用户检查成果。", "",
              "前置体验仍使用D02确定的可靠主体与部署范围，本机开发身份不能直接用于公网服务。P5补齐账号/设备部署、恢复评测和完整受控试用资料；实际对外发布另按届时用户授权执行。", "",
              "## 上线范围与实现范围分开", "", "| 能力 | 开发时安排 | 默认开放条件 |", "| --- | --- | --- |",
              "| 单Agent/固定模型 | P0/P1真实接线 | 已配置模型及对应实际权限，最小闭环已验收 |",
              "| local_runner / file_access / file_write / process_exec | P1，P3增强隔离/审阅 | 实际配对/用户项目选择/范围/环境/审批通过；支持能力分别报告 |",
              "| agents.create / agents.invoke | P2 | 定义与实例严格区分；只向有权限且可执行的任务暴露 |",
              "| DAG/多Agent并行 | P3 | 语义评估与资源/成本检查通过；不是所有任务自动最高规格 |",
              "| web_search / memory / extensions / MCP | P2/P4分批完成 | 已配置/授权/验收；私有连接、记忆读与贡献各自可关闭 |",
              "| environment_install | P4 | 批准模板/来源/网络/本机权限；P1先用真实预装Python环境 |",
              "| Auto模型政策 | P4 | 用户明确Auto授权及兼容候选；固定模型及缺省子Agent不可暗换 |",
              "| agent_handoff / automations | P5-04目标实现并验收 | 默认关闭，另定产品启用范围；不阻塞首次核心试用 |",
              "| 可选云执行后端 | P4-07按部署决定 | 未选则关闭且记not_implemented；不能把本地副本标成云沙箱 |",
              "| 推特包装 | P5-06后续设计 | 独立UAW先交付，范围明确后另排开发 |", "",
              "旗标键如需新增先在配置/接口契约登记；这张表不授权任何真实动作。所有开关在发现、调用、恢复和子Agent处一致校验。", "",
              "## 为什么先选Python样例", "",
              "它能以一条任务验证本地读取、写入、进程、真实测试、引用、变更、取消和审阅。这个工程验收样例不替代办公/开发/学术三类用户方向；P0收集三类材料，P2完成三个领域真实交付，P3以后用同一批样例做比较。", ""]
    write(path, lines)


def build_sequence():
    path = "docs/plan/SEQUENCE.md"
    lines = ["# 全局实施顺序与并行条件", "", link(path, "docs/plan/README.md", "模块索引") + " · " + link(path, "docs/plan/STAGES.md", "阶段门槛"), "",
             "模块页按职责查找，实际开工按本页依赖交替推进。轮号是推荐阅读顺序，开工取决于前置证据；同阶段满足依赖的独立任务可以并行开发。下一阶段的正式验收以先前核心阶段门槛通过为前提。", "",
             "当前已增加" + link(path, "docs/plan/PARALLEL.md", "4个session的组件分工") + "与" + link(path, "docs/plan/PARALLEL_WORKFLOW.md", "开工/合并规则") + "。组件开发依赖和整轮验收依赖分开记录，原50轮完整门槛保持有效。", "",
             "## 关键依赖与可并行部分", "", "| 范围 | 执行建议 |", "| --- | --- |",
             "| P0 | 工程→存储→配置→受理/账本→真实模型；先让开发环境和授权身份可靠 |",
             "| P1 | 理解/上下文/工具→Runner/实际环境/变更→单循环/核验→用户控制/真实页面→闭环验收；页面草图和fixture准备可提前 |",
             "| P2 | 文件→搜索与技能/定义→单子调用/Join；搜索P2-02与技能P2-03在P2-01后可独立推进，办公/学术汇合后验收 |",
             "| P3 | steps→DAG校验/调度后，工具并发P3-03与子Agent并发P3-04可分开开发；写合并/审阅/多会话仍按依赖继续 |",
             "| P4 | 内容依赖/检索/缓存/连接治理先接稳；P4-06后环境P4-07与Auto P4-08可独立推进，完整页面汇合 |",
             "| P5 | 检查点→恢复→评测/试用资料；P5-04可与评测准备独立推进但不挡首次试用，推特设计继续后置 |", "",
             "这里的并行是团队实施安排，不强制运行中多Agent。共同修改schema/配置/公共契约时要协调版本，不能因开发可并行就跳过Runtime资源隔离。", "", "## 所有轮次与有效前置", "",
             "有效前置包含显式工作包依赖和上一阶段核心门槛。", "", "| 轮次/模块 | 本轮目标 | 有效前置 |", "| --- | --- | --- |"]
    for r in ROUNDS:
        deps = "、".join(round_link(path, id) for id in effective_dependencies(r)) or "无"
        lines.append(f"| {round_link(path, r['id'], True)} / {MODULES[r['module']][0]} | {r['goal']} | {deps} |")
    lines += ["", "## 缺外部条件时怎样继续", "",
              "- 缺提供方配置：可核对schema、适配器协议和受控fixture；实际调用门槛仍待配置。",
              "- 未确定存储/前端/部署：可做ports、任务材料和独立职责代码；涉及权威数据、真实界面或执行环境的轮不能凭测试替身验收。",
              "- 某轮失败：记录具体失败、保留已确认成果，只开放不依赖失败部分的工作包。",
              "- 改范围或拆子轮：同时修catalog中的依赖、节点和验收，再重建计划；不要直接改生成文件让链路脱节。", ""]
    write(path, lines)


def build_decisions():
    path = "docs/plan/DECISIONS.md"
    lines = ["# 待定项与最晚决策轮", "", link(path, "docs/plan/README.md", "计划索引"), "",
             "各模块技术主选已形成，见 " + link(path, "TECHNOLOGY_STACK.md", "技术栈") + "。以下记录待实际兼容验证的组合，以及历史权威位置、提供方、格式和启用范围等产品/部署待定项；不能把主选设计当作已经联测通过。实际依据与结果写入 `docs/decisions/`。", "",
             "| ID | 需要决定什么 | 最晚相关轮 | 当前状态 |", "| --- | --- | --- | --- |"]
    for d in DECISIONS:
        lines.append(f"| {d['id']} | {d['question']} | {round_link(path, d['before'])} | {d['status']} |")
    for d in DECISIONS:
        lines += ["", f"## {d['id']} · {d['question']}", "", f"- 影响：{d['impact']}", f"- 决策前/未确定时：{d['fallback']}", f"- 最晚记录点：{round_link(path, d['before'], True)}；后续轮若再次依赖本项，要核对实际结论和当前配置。"]
    lines += ["", "模型、搜索或MCP提供方协议实施时按批准候选核对官方资料；计划不预设可随时取得API或自动安装任意包。语义验收和经济阈值需先登记，再比较单Agent/多Agent/Auto/缓存，不事后调整成通过。", ""]
    write(path, lines)


def build_coverage(node_map):
    path = "docs/plan/COVERAGE.md"
    lines = ["# 架构节点 → 开发轮次覆盖", "", link(path, "docs/plan/README.md", "开发计划") + " · " + link(path, "docs/design/README.md", "策略索引"), "",
             f"{len(NODES)}个节点均有计划关联。同一节点可在多个阶段完善；这里证明排入工作包，不证明全部功能已经实现。根节点聚合不把后续子能力算作早期完成。", "",
             "| 节点与作用 | 实施/完善轮 | 策略/接口 | 目标代码 |", "| --- | --- | --- | --- |"]
    for id, n in NODES.items():
        rounds = "、".join(round_link(path, r) for r in node_map[id]["rounds"])
        refs = link(path, DESIGNS[id]["design_doc"], "策略") + " / " + link(path, INTERFACES[id]["interface_doc"], "接口")
        lines.append(f"| `{id}` · {n['label']} | {rounds} | {refs} | `{code_target(id)}` |")
    lines += ["", "每个节点完成状态最终应细分实际支持的分支、默认关闭的扩展、未选后端和未通过案例。机器映射只有rounds和相关文档，不生成implemented=true。", ""]
    write(path, lines)


def build_interface_assignments():
    path = "docs/plan/INTERFACE_ASSIGNMENTS.md"
    lines = ["# 接口关联开发工作包", "", link(path, "docs/plan/README.md", "计划入口") + " · " + link(path, "docs/api/README.md", "完整接口定义"), "",
             f"{len(OPERATIONS)}个接口按其架构节点反查相关轮次。**关联不是一次性实施承诺，也不是接口就绪表。** ui/ingress/Runtime根聚合会把早期轮和晚期轮同时列出；实际可调用分支必须由具体轮任务、能力状态及验收证据判断。", "",
             "相同ID在不同channel下是不同接口，以 `(channel,id)` 定位。请求/返回字段以逐接口文档和对象字典为准。", "",
             "| 接口/传输 | 请求 → 业务返回 | 相关轮次 |", "| --- | --- | --- |"]
    for o in OPERATIONS:
        matched = [r["id"] for r in ROUNDS if set(r["nodes"]).intersection(o["nodes"])]
        doc = next(x["doc"] for n in o["nodes"] for x in INTERFACES[n]["interfaces"] if x["id"] == o["id"] and x["channel"] == o["channel"])
        lines.append(f"| {link(path, doc, o['id'])} / {CHANNELS[o['channel']]} | `{o['request']}` → `{o['response']}` | {'、'.join(round_link(path, r) for r in matched)} |")
    lines += ["", "未实现接口返回明确不可用或不注册；状态/授权字段由可信调用上下文注入。不能为了让表格看似全绿而生成自动成功占位函数。", ""]
    write(path, lines)


def build_template_and_status():
    write("docs/plan/ROUND_TEMPLATE.md", ["# 每轮开发与验收记录模板", "", "本模板复制到 `docs/implementation/<轮次>.md`；已有实施记录独立维护。计划任务来自对应round文档，实际信息在报告中填写。", "",
          "## 1. 工作包", "", "- 轮次/标题/计划页：", "- 负责人/实际开始/实际完成：", "- 当前状态：planned / in_progress / blocked / accepted。deferred用于明确后置范围。", "- 实际代码基线/ReleaseManifest/依赖版本：", "",
          "- 多session场景另填Session/子包/允许目录/真实提交SHA，使用 [交接模板](../coordination/HANDOFF_TEMPLATE.md)；组件接受不自动改变整轮验收。", "",
          "## 2. 开始条件", "", "- 前置轮及验收证据：", "- 本轮需要的已决定ADR/配置/权限/设备/提供方：", "- 原始场景、初态及用户未提交改动：", "- 未满足项与仍可推进的独立任务：", "",
          "## 3. 实际修改", "", "| 任务 | 设计/接口依据 | 实际代码文件 | 支持范围/未实现分支 |", "| --- | --- | --- | --- |", "| 待填 | 待填 | 待填 | 待填 |", "",
          "## 4. 验收与证据", "", "| 验收条件 | 实际方法/命令/审阅 | 材料/版本/回执位置 | 结果及限制 |", "| --- | --- | --- | --- |", "| 待填 | 待填 | 待填 | 未执行 |", "",
          "语义核验记录用户要求与实际证据的关系，不记录或要求模型私密思维链。真实操作回执与受控mock用例分别注明；包括全部尝试成本和用户检查/返工时间。", "",
          "## 5. 问题与回退", "", "- 失败所在模块/operation/attempt/版本：", "- 未决外部效果及对账状态：", "- 对用户文件/成果/后续轮的影响：", "- 实际回滚/补偿方式及不可撤销范围：", "",
          "## 6. 验收结论", "", "- 本轮是否满足全部退出条件：", "- 未通过项/默认关闭能力/未选后端：", "- 可开放的下一轮及原因：", "- 用户接受结果（与AI完成判断分开）：", "",
          "只有实际证据齐全才将planning/catalog.py中的本轮状态改为accepted并填implementation_evidence；随后重建计划。不能把编写文档、空目录、Mock或flag关闭记作实现。", ""])
    path = "docs/plan/STATUS.md"
    counts = Counter(r["status"] for r in ROUNDS)
    lines = ["# 开发计划当前状态", "", link(path, "docs/plan/README.md", "总索引"), "", f"计划记录日期{DATE}：" + "、".join(f"{STATUS_LABELS[k]}{v}轮" for k, v in counts.items()) + f"。已验收轮数：{counts.get('accepted', 0)}。", "",
             "Context/Tool/Runner首包已合入，Context理解接线已通过；Agent业务循环、apps/web与真实Runner配对/执行仍待建设。当前能力与启动方式见" + link(path, "docs/implementation/README.md", "实际实施入口") + "。文档检查只核对引用/覆盖/依赖，不能替代运行证据。", "", "| 轮次 | 当前状态 | 范围 | 实现证据 |", "| --- | --- | --- | --- |"]
    for r in ROUNDS:
        evidence = "、".join(link(path, ref, ref) for ref in r["implementation_evidence"]) or "为空；没有实现完成声明"
        lines.append(f"| {round_link(path, r['id'], True)} | {STATUS_LABELS[r['status']]} | {SCOPE_LABELS[r['scope']]} | {evidence} |")
    lines += ["", "P5-04的‘实现后默认关闭’是交付目标，目前同样未开发；P5-06为后续讨论的适配设计。云执行是否建设待定。核心试用资料的最后门槛是P5-07，完整扩展目标还需P5-04另行验收。", ""]
    write(path, lines)


def source_checks():
    errors = []
    if len(ROUND_BY_ID) != len(ROUNDS):
        errors.append("duplicate round ID")
    if len(DECISION_BY_ID) != len(DECISIONS):
        errors.append("duplicate decision ID")
    for r in ROUNDS:
        if r["phase"] not in PHASES or r["module"] not in MODULES:
            errors.append(f"unknown phase/module: {r['id']}")
        if r["status"] not in STATUS_LABELS or r["scope"] not in SCOPE_LABELS:
            errors.append(f"unknown status/scope: {r['id']}")
        if not r["tasks"] or not r["acceptance"] or not r["deliverables"]:
            errors.append(f"incomplete work package: {r['id']}")
        if r["status"] == "accepted" and not r["implementation_evidence"]:
            errors.append(f"accepted without evidence: {r['id']}")
        for d in r["depends_on"]:
            if d not in ROUND_BY_ID:
                errors.append(f"unknown dependency: {r['id']}->{d}")
            elif d >= r["id"]:
                errors.append(f"dependency not earlier: {r['id']}->{d}")
        for n in r["nodes"]:
            if n not in NODES or n not in DESIGNS or n not in INTERFACES:
                errors.append(f"unknown/unmapped node: {r['id']}->{n}")
        for d in r["decision_dependencies"]:
            if d not in DECISION_BY_ID:
                errors.append(f"unknown decision: {r['id']}->{d}")
        for ref in r["implementation_evidence"]:
            if not (ROOT / ref).is_file():
                errors.append(f"missing implementation evidence: {r['id']}->{ref}")
    for d in DECISIONS:
        if d["before"] not in ROUND_BY_ID:
            errors.append(f"unknown decision checkpoint: {d['id']}")
        elif d["id"] not in ROUND_BY_ID[d["before"]]["decision_dependencies"]:
            errors.append(f"decision checkpoint lacks reference: {d['id']}")
    covered = {n for r in ROUNDS for n in r["nodes"]}
    errors.extend(f"node has no development round: {n}" for n in set(NODES) - covered)
    visiting, visited = set(), set()

    def visit(id):
        if id in visiting:
            errors.append(f"dependency cycle: {id}")
            return
        if id in visited:
            return
        visiting.add(id)
        for dep in effective_dependencies(ROUND_BY_ID[id]):
            if dep in ROUND_BY_ID:
                visit(dep)
        visiting.remove(id)
        visited.add(id)

    for id in ROUND_BY_ID:
        visit(id)
    reachable = set()

    def collect(id):
        if id in reachable:
            return
        reachable.add(id)
        for dep in effective_dependencies(ROUND_BY_ID[id]):
            if dep in ROUND_BY_ID:
                collect(dep)

    collect(PHASE_GATES["P5"])
    for r in ROUNDS:
        if r["scope"] == "required" and r["id"] not in reachable:
            errors.append(f"core round missing from final core gate dependencies: {r['id']}")
        if r["scope"] != "required" and r["id"] in reachable:
            errors.append(f"non-core round blocks first core trial: {r['id']}")
    for o in OPERATIONS:
        if not any(set(r["nodes"]).intersection(o["nodes"]) for r in ROUNDS):
            errors.append(f"interface has no round association: {o['channel']}:{o['id']}")
    return errors


def check_links(paths):
    errors, count = [], 0
    for path in paths:
        target = ROOT / path
        if not target.is_file() or target.suffix != ".md":
            continue
        content = target.read_text(encoding="utf-8")
        for label, dest in re.findall(r"\[([^\]]+)\]\(([^\)]+)\)", content):
            if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", dest) or dest.startswith("#"):
                continue
            dest = dest.split("#", 1)[0].strip("<>")
            if not dest:
                continue
            count += 1
            resolved = (target.parent / dest).resolve()
            if not resolved.is_file():
                errors.append(f"missing document link: {path} -> {dest}")
    return errors, count


def main():
    errors = source_checks()
    if errors:
        raise SystemExit("\n".join(errors))
    node_map = {id: {"rounds": [r["id"] for r in ROUNDS if id in r["nodes"]], "plan_documents": [round_path(r["id"]) for r in ROUNDS if id in r["nodes"]], "design_doc": DESIGNS[id]["design_doc"], "interface_doc": INTERFACES[id]["interface_doc"], "code_target": code_target(id), "implementation_evidence": []} for id in NODES}
    write_json("planning/plan.json", {"plan_version": "0.1", "architecture_version": GRAPH["architecture_version"], "date": DATE, "status": "development_plan_only", "module_groups_are_services": False, "interface_associations_are_readiness": False, "modules": {id: {"name": v[0], "responsibility": v[1]} for id, v in MODULES.items()}, "phases": PHASES, "phase_gates": PHASE_GATES, "decisions": DECISIONS, "rounds": [round_record(r) for r in ROUNDS]})
    write_json("planning/plan-map.json", {"plan_version": "0.1", "date": DATE, "status": "planned_coverage_only", "nodes": node_map})
    for r in ROUNDS:
        build_round(r)
    for module in MODULES:
        build_module(module)
    build_readme()
    build_stages()
    build_sequence()
    build_decisions()
    build_coverage(node_map)
    build_interface_assignments()
    build_template_and_status()
    report_path = "docs/plan/plan-check.json"
    (ROOT / report_path).write_text("{}\n", encoding="utf-8")
    extra = ["DEVELOPMENT_PLAN.md", "README.md", "docs/DOCUMENT_MAP.md", "docs/PROJECT_STRUCTURE.md"]
    link_errors, link_count = check_links(GENERATED + extra)
    errors += link_errors
    report = {"status": "passed" if not errors else "failed", "date": DATE, "plan_rounds": len(ROUNDS), "phase_counts": dict(Counter(r["phase"] for r in ROUNDS)), "module_groups": len(MODULES), "scope_counts": dict(Counter(r["scope"] for r in ROUNDS)), "status_counts": dict(Counter(r["status"] for r in ROUNDS)), "planned_node_coverage": {"covered": len(node_map), "total": len(NODES)}, "interface_associations": len(OPERATIONS), "dependency_graph_acyclic": not any("cycle" in e for e in errors), "final_core_gate_covers_required_rounds": not any("core round missing" in e for e in errors), "optional_rounds_do_not_block_first_core_trial": not any("non-core round blocks" in e for e in errors), "local_document_links_checked": link_count, "generated_files": len(GENERATED) + 1, "errors": errors, "runtime_implementation": "not_started" if not (ROOT / "src/uaw/application.py").is_file() else "not_inferred_from_plan_checks", "runtime_behavior_tests": "not_run_by_plan_generator", "limitations": ["coverage means planned association, not implementation or interface readiness", "code paths are planned and intentionally not validated as existing implementations", "no schedule/team capacity estimate or provider availability is inferred", "local link checks validate file existence, not Markdown anchor validity"]}
    write_json(report_path, report)
    print(json.dumps({k: report[k] for k in ["status", "plan_rounds", "phase_counts", "planned_node_coverage", "interface_associations", "local_document_links_checked", "errors"]}, ensure_ascii=False))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    from build_parallel import main as build_parallel
    build_parallel()
    main()
