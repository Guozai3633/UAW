"""Generate detailed design documents from authored policies and graph IDs."""
import json
import os
from pathlib import Path
from catalog import BASES, MODULES, MODEL_STAGES, SOURCES, STRATEGIES

ROOT = Path(__file__).resolve().parents[1]
GRAPH = json.loads((ROOT / "architecture/graph.json").read_text(encoding="utf-8"))
NODES = GRAPH["nodes"]
INTERFACE_MAP_PATH = ROOT / "contracts/interface-map.json"
INTERFACES = json.loads(INTERFACE_MAP_PATH.read_text(encoding="utf-8"))["nodes"] if INTERFACE_MAP_PATH.exists() else {}


def doc_target(id):
    folder = "modules" if id in MODULES else "components"
    return f"docs/design/{folder}/{id.replace('.', '-')}.md"


def code_target(id):
    root, *parts = id.split(".")
    base = BASES[root]
    if root == "ui":
        return base + "/"
    if root == "ingress":
        return base + "/ingress.py"
    if id == "support":
        return base + "/__init__.py"
    if id == "agent.definitions":
        return base + "/definitions/facade.py"
    if id == "run.resume.continue":
        return base + "/resume/continue_run.py"
    if not parts:
        return base + "/facade.py"
    if id in GRAPH["views"]:
        return base + "/" + "/".join(parts) + "/facade.py"
    return base + "/" + "/".join(parts) + ".py"


def link(from_path, to_path, label):
    return f"[{label}]({os.path.relpath(ROOT / to_path, (ROOT / from_path).parent).replace(os.sep, '/')})"


def write(path, lines):
    target = ROOT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")


def neighbors(id):
    found = []
    for v in GRAPH["views"].values():
        for e in v["edges"]:
            if id in (e["source"], e["target"]):
                signature = (e["source"], e["target"], e["kind"], e["label"])
                if signature not in found:
                    found.append(signature)
    return found


def related(id, path):
    edges = neighbors(id)
    lines = ["## 模块联系", "", "| 方向 | 关系与载荷 | 对应设计 |", "| --- | --- | --- |"]
    for source, target, kind, label in edges:
        other = target if source == id else source
        direction = "本节点 → 下游" if source == id else "上游 → 本节点"
        lines.append(f"| {direction} | {GRAPH['types'][kind]}：{label} | {link(path, doc_target(other), NODES[other]['label'])} |")
    if not edges:
        lines += ["| 父模块调度 | 按父级公共契约调用，不单独成为服务 | 见父级设计 |"]
    return lines + [""]


def interfaces_section(id,path):
    if id not in INTERFACES:return []
    return ["## 逐字段接口与对象定义", "", link(path,INTERFACES[id]["interface_doc"],"本节点全部接口")+" · "+link(path,"docs/api/OBJECTS.md","统一对象字典")+" · "+link(path,"docs/api/CONVENTIONS.md","接口共同规则"), "",
            "上面的领域字段用于说明策略。准确请求DTO、动作分支、必填性、返回对象和结构规则以接口契约源contracts/interface_catalog.py及其生成schema为准；语义/权限/版本/执行策略仍按本设计落实。出现差异需同时修维护源，不能拿摘要字段替代当前接口校验。", ""]


def source_section(id):
    root = id.split(".")[0]
    return ["## 参考与需要验证的选择", "", *[f"- [{label}](https://app.notion.com/p/{pid})：参考问题与原则，具体协议为 UAW 自己的设计。" for label, pid in SOURCES[root]],
            "", "题集是检查遗漏的来源，未逐题验证第三方技术结论。实施阶段涉及具体供应商协议时再核对其官方资料；本文的字段、算法顺序与权限边界不是从题集自动取得的事实。", ""]


def children_section(id, path):
    children = [n for n, v in NODES.items() if v["parent"] == id]
    if not children:
        return []
    return ["## 内部模块与目录", "", "| 子模块 | 详细开发策略 | 计划代码文件 |", "| --- | --- | --- |",
            *[f"| {NODES[c]['label']} | {link(path, doc_target(c), c)} | `{code_target(c)}` |" for c in children], ""]


def component(id):
    n = NODES[id]
    s = STRATEGIES[id]
    path = doc_target(id)
    class_name = "".join(word.capitalize() for word in id.replace(".", "_").split("_"))
    lines = [f"# {n['label']}：开发设计", "", f"节点 `{id}` · UAW v0.10 · 2026-10-07 · 状态：待实现/待任务验证。", "",
             link(path, "docs/design/README.md", "开发设计索引") + " · " + link(path, "docs/design/COMMON_CONTRACTS.md", "公共契约") + " · " + link(path, "ARCHITECTURE_ATLAS.md", "关系图谱"), "",
             "## 职责与代码位置", "", n["description"], "", f"- 计划主文件：`{code_target(id)}`。", f"- 统一业务入口：`{n['entry']}`；只允许所属 facade 或获准适配器调用。", f"- 上层归属：`{n['parent'] or '产品边界'}`。该节点是逻辑组件，不默认独立服务。", f"- 硬约束：{n['guard']}", "",
             "## 输入、输出与调用协议", "", f"输入请求 `{class_name}Request` 的领域字段（实验类型，实施时落在所属目录的 contracts.py）：", "",
             "```text", s["payload"], "```", "", f"领域输出：{n['outputs']}。结果使用 `ComponentResult[领域载荷]`；本节点只填实际确认的 `output_refs/revision`，等待、拒绝、冲突、取消和失败均为显式类型。", "",
             "关联、主体与预算通过 TrustedExecutionContext 注入，不能由模型业务参数覆盖。请求/结果的公共字段与持久化边界见 COMMON_CONTRACTS；传入路径/文字不隐含访问授权。", "",
             "## 详细处理策略", ""]
    lines += [f"{i}. {step}。" for i, step in enumerate(s["steps"], 1)]
    lines += ["", "### 模型参与方式", "", "需要语义判断时，由当前继承模型提出建议；可复用当前主调用或按需发起，不强制专门判断 Agent。技术验证与状态提交仍由代码执行。" if id in MODEL_STAGES else "本组件的契约和状态处理由代码执行。涉及上游模型内容时把它作为待验证提案或数据，不再自动启动一个决策模型。",
              "", "## 状态、并发与提交", "", s["commit"], "", "同一逻辑请求保持request_id；重试另有attempt_id。持久修改使用预期领域版本/事务或持久执行意图；读取保持实际来源版本。Run事件只引用本节点确认的变化，不能先播成功再尝试提交。", "",
              "## 失败分支与反馈", "", *[f"- {error}。" for error in s["errors"]], "", "返回 Failure(code、retryable、failed_phase、recover_hint、evidence_refs)。代码只能恢复明确安全的执行错误；改变用户目标、模型、权限或非等价能力必须回 Agent/用户。", "",
              "## 缓存、成本与取消", "", s["efficiency"], "", "使用原Run总预算和剩余deadline。取消先停止新动作，再等待执行器实际回执；已经发生的副作用不随文档/聊天回退撤销。引用读取始终复核当前授权/删除。", "",
              "## 开发验收案例", "", *[f"- {case}。" for case in s["acceptance"]], "", "这些是待实现的验收要求，本轮未运行 Runtime 行为测试。首个场景用真实输入/输出/环境建立fixture；权限、版本、取消与副作用用可重复硬检查，语义标准按人工样本校准。", ""]
    lines += interfaces_section(id,path) + children_section(id, path) + related(id, path) + source_section(id)
    write(path, lines)


def module(id):
    n, s = NODES[id], MODULES[id]
    path = doc_target(id)
    lines = [f"# {n['label']}：模块开发设计", "", f"节点 `{id}` · UAW v0.10 · 2026-10-07 · 状态：目标设计，Runtime 未实现。", "",
             link(path, "docs/design/README.md", "开发设计索引") + " · " + link(path, "docs/PROJECT_STRUCTURE.md", "目录设计") + " · " + link(path, "docs/design/COMMON_CONTRACTS.md", "公共契约"), "",
             "## 统一入口与状态所有权", "", f"计划包：`{BASES[id]}/`，入口：`{code_target(id)}`。", "", f"入口契约：`{s['entry']}`。", "", "所有权：" + s["owner"], "",
             "## 内部组织策略", "", s["strategy"], "", "facade接收可信请求并协调子组件；子组件不直接调用其他Runtime的私有实现。只通过注入的port调用邻域公开入口。Python首阶段组合在同一进程内，持久化和本地Runner执行仍通过边界接口。", "",
             "## 数据与依赖接口", "", "输入：" + n["inputs"] + "。输出：" + n["outputs"] + "。", "", "注入ports：`" + s["ports"] + "`。", "", "领域类型放本包 contracts.py；模型可见工具schema由Tool消费。Repository不暴露其他模块可任意写本模块对象的方法，修改必须走本模块业务入口。", "",
             "## 决策、权限与资源策略", "", s["models"], "", n["guard"], "", "每次提交绑定真实版本、当前scope、剩余deadline和预算。固定常规配置与当前撤销分开检查。多模块提交用本地事务或可恢复意图，不能承诺外部动作exactly-once。", "",
             "## 失败与恢复策略", "", "facade保留失败发生阶段与原始受控引用。参数/依赖/版本冲突回调用者修复；拒绝不通过换工具绕过；副作用unknown先Tool对账。恢复先检查此领域schema/版本兼容，再恢复可继续边界，不用Trace重建权威状态。", "",
             "## 文件组织规则", "", "- `facade.py`：统一入口、依赖注入、调用编排。", "- `contracts.py`：领域请求/结果/版本化对象。", "- `ports.py`：存储、跨Runtime与执行器协议。", "- 子组件文件/包：实现具体策略，分层节点有自己的facade/contracts/ports。", "- `repository.py`：领域存储适配，实现CAS和幂等；业务规则仍在组件。", "- `tests/unit/` 与 `tests/integration/`：实现阶段只验证具体风险/门槛，不复制实现。", "",
             "## 实施与验收门槛", "", s["gate"], "", "首条真实任务贯通入口/核心子组件；其他节点先保留port，未实现能力不暴露为可调用工具。细分模块策略与验收案例见下面各文档。", ""]
    if id == "support":
        lines = [line.replace("facade接收可信请求并协调子组件；", "各支撑设施通过独立公共入口接收可信请求；").replace("facade保留失败发生阶段", "各设施入口保留失败发生阶段").replace("- `facade.py`：统一入口、依赖注入、调用编排。", "- `__init__.py`：导出各独立设施入口；不实现万能facade或固定支撑流水线。") for line in lines]
    lines += interfaces_section(id,path) + children_section(id, path) + related(id, path) + source_section(id)
    write(path, lines)


def main():
    expected = set(NODES)
    actual = set(STRATEGIES) | set(MODULES)
    assert expected == actual, {"missing": sorted(expected - actual), "extra": sorted(actual - expected)}
    for id, s in STRATEGIES.items():
        assert len(s["steps"]) >= 3 and len(s["errors"]) >= 2 and len(s["acceptance"]) >= 2, id
    mapping = {}
    for id in NODES:
        (module if id in MODULES else component)(id)
        mapping[id] = dict(design_doc=doc_target(id), code_target=code_target(id),
                           root=id.split(".")[0], implemented=False)
    write("design/design-map.json", [json.dumps(dict(architecture_version="0.10", date="2026-10-07", nodes=mapping), ensure_ascii=False, indent=2)])
    lines = ["# UAW 开发设计总索引", "", "状态：v0.10 · 2026-10-07。每个图节点有单独文档与计划代码位置；所有代码目标均待实现，文档覆盖不代表实现或已完成任务验证。", "",
             "[全局指引](../../README.md) · [项目目录](../PROJECT_STRUCTURE.md) · [文档作用地图](../DOCUMENT_MAP.md) · [公共契约](COMMON_CONTRACTS.md) · [子Agent完整链路](SUBAGENT_LIFECYCLE.md)", "",
             "## 从哪里开始", "", "1. 先看 SUBAGENT_LIFECYCLE 和 PROJECT_STRUCTURE，确认端到端行为与开发组织。", "2. 再看 modules/ 下对应大模块，进入其 components/ 子节点文档。", "3. 图谱节点中的‘开发设计’链接与下表完全对应。修改策略先改 design/catalog.py，再重建文档和图谱。", ""]
    for root in BASES:
        lines += [f"## {NODES[root]['label']}", "", "| 节点 | 开发策略文档 | 计划代码位置 |", "| --- | --- | --- |"]
        for id, n in NODES.items():
            if id.split(".")[0] == root:
                lines.append(f"| `{id}` | {link('docs/design/README.md', doc_target(id), n['label'])} | `{mapping[id]['code_target']}` |")
        lines.append("")
    write("docs/design/README.md", lines)
    print(json.dumps({"nodes": len(NODES), "mapped": len(mapping), "module_docs": len(MODULES), "component_docs": len(STRATEGIES)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
