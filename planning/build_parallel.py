"""Build the session plan and check ownership/dependencies; never start sessions or Git worktrees."""

import json
import os
import re
from pathlib import Path

from catalog import ROUNDS
from parallel_catalog import (BASELINE, CONFIGURATIONS, DATE, PACKAGES, SESSIONS,
                              SESSION_PROGRESS, PACKAGE_PROGRESS, VERSION)

ROOT = Path(__file__).resolve().parents[1]
GENERATED = []


def write(path, value):
    target = ROOT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(value.rstrip() + "\n", encoding="utf-8")
    GENERATED.append(path)


def link(from_path, target, label):
    return f"[{label}]({os.path.relpath(ROOT / target, (ROOT / from_path).parent).replace(os.sep, '/')})"


def overlap(left, right):
    return left == right or (left.endswith("/") and right.startswith(left)) or (right.endswith("/") and left.startswith(right))


def validate():
    errors = []
    round_ids = {r["id"] for r in ROUNDS}
    package_by_id = {p["id"]: p for p in PACKAGES}
    if len(package_by_id) != len(PACKAGES):
        errors.append("duplicate package ID")
    for index, (left_key, left) in enumerate(SESSIONS.items()):
        for right_key, right in list(SESSIONS.items())[index + 1:]:
            for left_path in left["owns"]:
                for right_path in right["owns"]:
                    if overlap(left_path, right_path):
                        errors.append(f"ownership overlap: {left_key}/{right_key}: {left_path}/{right_path}")
    def visit(key, stack):
        if key in stack:
            errors.append(f"package dependency cycle: {key}")
            return
        for dependency in package_by_id[key]["deps"]:
            if dependency not in package_by_id:
                errors.append(f"missing package: {dependency}")
            else:
                visit(dependency, stack | {key})
    for package in PACKAGES:
        visit(package["id"], set())
        if package["session"] not in SESSIONS:
            errors.append(f"unknown session: {package['id']}")
        if set(package["rounds"]) - round_ids:
            errors.append(f"unknown round: {package['id']}")
        if package["scope"] in ("independent_component", "optional_component") and package["deps"] != ["MS-00"]:
            errors.append(f"first component has an undeclared worker dependency: {package['id']}")
    for key, session in SESSIONS.items():
        for package_id in session["starts"] + session["later"]:
            if package_id not in package_by_id or package_by_id[package_id]["session"] != key:
                errors.append(f"bad session assignment: {key}/{package_id}")
        for path in session["owns"]:
            if path.startswith("/") or ".." in Path(path).parts or "\\" in path:
                errors.append(f"invalid ownership path: {path}")
    return errors


def build_sessions():
    for key, session in SESSIONS.items():
        path = f"docs/plan/sessions/{key}.md"
        ready = BASELINE.get("workspaces_ready", False) and key in ("A", "B", "C", "D")
        progress = SESSION_PROGRESS[key]
        state = "状态：" + progress["state"] + "以DISPATCH的固定版本与派发为准。"
        lines = [f"# Session {key}：{session['name']}", "", link(path, "docs/plan/PARALLEL.md", "并行开发总入口"), "",
                 state, "",
                 "## 工作位置和顺序", "", f"- {'实际' if ready else '建议'}分支：`{session['branch']}`。", f"- {'实际' if ready else '建议'}worktree：`{session['worktree']}`。",
                 f"- 首包：{'、'.join(session['starts'])}；后续：{'、'.join(session['later']) or '本轮无'}。",
                 f"- 交接记录：{link(path, session['report'], session['report'])}。",
                 f"- 公共变更提案目录：`{session['request_dir']}`。", "", "## 可修改路径", "",
                 *[f"- `{target}`" for target in session["owns"]], "", "忽略的本session缓存、临时目录和测试回执可写；可修改路径以本session工作区为根。工作目录之外的其他worktree仍不可修改。", "",
                 "## 具体边界", "", *[f"- {rule}" for rule in session["rules"]], "",
                 "公共schema/port/依赖有缺口时，提交有字段、示例、错误语义和受影响调用方的提案，A合入并发布新基线后再使用；不在私有DTO中偷偷加不兼容字段。", "",
                 "## 对应工作包", ""]
        for package in [p for p in PACKAGES if p["session"] == key]:
            lines += [f"### {package['id']}：{package['title']}", "",
                      "对应原轮：" + "、".join(link(path, f"docs/plan/rounds/{r}.md", r) for r in package["rounds"]) + "。",
                      "开发前置：" + ("、".join(package["deps"]) or "本session收尾与初始化工作") + "。", "",
                      "任务：", "", *[f"{i}. {task}" for i, task in enumerate(package["tasks"], 1)], "",
                      "交付检查：", "", *[f"- {condition}" for condition in package["acceptance"]], ""]
        lines += ["## 可复制到新session的开工说明", "", "下面只启动本session任务；用户在独立工作区新建聊天后粘贴。A先在DISPATCH公布真实基线SHA和派发包。", "", "```text",
                  f"你负责UAW并行开发中的Session {key}：{session['name']}。",
                  f"当前工作目录必须是{session['worktree']}，分支必须是{session['branch']}。",
                  f"先阅读README.md、docs/plan/PARALLEL.md、docs/plan/PARALLEL_WORKFLOW.md和docs/plan/sessions/{key}.md。",
                  "读取docs/coordination/DISPATCH.md。首次开工核对HEAD与parallel-wave-1解析出的commit相同；后续按A发布的新基线同步。",
                  (f"当前执行{progress['package']}。工作区干净后fetch origin --tags，将ms-i1合入本工作分支，保留已有提交历史。"
                   if progress["ready"] else f"当前{progress['package']}未派发；只整理现有交接与依赖提案，不开始需要未发布依赖的实现。"),
                  "只修改session页的允许目录。涉及公共文件，写入本session requests目录，说明最小变更与消费方影响。",
                  "按照工作包完成代码和必要验证，未实现依赖明确返回不可用；测试替身不冒充真实LLM/Runner。",
                  "保持原文、固定用户模型、权限/flag、取消、幂等及版本边界。未经确认的D01/D03/D06不自行设定。",
                  "在handoff记录写实际分支与提交SHA、改动文件、公开接口、验证命令/回执、未通过项和接线要求。",
                  "开发session只提交自己的改动。A审阅、合入、处理公共冲突并执行整条链路回归。不要自行创建其他session。",
                  "```", ""]
        write(path, "\n".join(lines))


def build_overview():
    path = "docs/plan/PARALLEL.md"
    lines = ["# UAW 多session开发计划", "", f"v{VERSION} · {DATE} · 方案：**3个开发session＋1个集成session，共4个**。", "",
             "先让不同session各做一个不重叠的组件包，再由集成session接起来。接口文档使组件能按同一规则开发；完整任务能运行，还需要具体文件归属、固定代码版本和组合验证。", "",
             "## 1. 当前起点", "",
             "- P0-01、P0-03、P0-04已验收；P0-02开发存储已验证，D01最终权威位置待定。",
             "- P0-05模型网关已实现；真实模型/API凭据尚未配置，D06及真实LLM验收未完成。",
             "- P1-01原文/逐字来源、理解版本、修订、取消、幂等与当前frame读取的协议检查通过；真实模型语义验收仍待D06。",
             f"- 当前全量{BASELINE['last_verified_tests']}项通过，无跳过；真实PostgreSQL＋受控模型响应，未运行实际Agent/Runner任务。",
             f"- `E:/UAW`已建立`integration`分支，`origin`关联`{BASELINE['remote']}`。",
             "- **B/C/D首包已分别合入；MS-I1完成开发范围，新基线为`ms-i1`。** B同步后执行MS-C2；A继续MS-I2；C/D的下一包等待公共依赖。实际接受与派发见" + link(path, "docs/coordination/DISPATCH.md", "统一派发表") + "。", "",
             "沿用原三个worktree，开发session自行在包边界同步固定标签；A不改写worker分支。具体见" + link(path, "docs/plan/PARALLEL_WORKFLOW.md", "开工、合并与交接流程") + "。", "",
             "## 2. 首批session", "", "| Session | 做什么 | 首个包 | 实际分工 |", "| --- | --- | --- | --- |"]
    for key, session in SESSIONS.items():
        lines.append(f"| {link(path, f'docs/plan/sessions/{key}.md', key + '：' + session['name'])} | {session['rules'][0]} | {'、'.join(session['starts'])} | {'第5个可选' if key == 'E' else '推荐4个方案'} |")
    lines += ["", "A既负责当前Intent收尾，也负责后续集成；不额外承担所有模块的开发。B/C/D遇到业务问题自己修复，A集中处理公共接线和归属冲突。", "",
              "## 3. 为什么这些部分现在可以并行", "", "| 子包 | 首包真正依赖 | 此时暂不接入的部分 |", "| --- | --- | --- |",
              "| MS-C1 上下文规则/来源/预算 | 已固定InstructionSet、ContextSnapshot、Scope、Ref和模型窗口契约 | 通用Context到Intent/Model的组装、Runner读文件 |",
              "| MS-T1 工具注册/过滤/schema | 已固定ToolSpec、ToolCall、CapabilityPolicy、flag和错误契约 | 审批、真实Runner派发及全链路结算 |",
              "| MS-R1 Runner协议/授权范围 | 已固定RunnerCommand/Receipt、RootSelection及可信上下文 | 实际账号配对、真实签名、安装/写入/exec授权 |", "",
              "这里的“无依赖”指首批组件包互不依赖另一个开发session的未完成代码。它们共同依赖MS-00发布的稳定基线。P1-02/03/04整轮本来有依赖，不能直接宣称三整轮都无依赖。", "",
              "**原50轮主计划和阶段验收门槛继续有效。** 子包可提前开发；整轮接受、能力启用和真实场景验收仍要满足原轮依赖，P0-05待配置的门槛不会因并行安排消失。", "",
              "## 4. 第一波与第二波", "", "```mermaid", "flowchart TD",
              "  A0[\"A：P1-01收尾、验证、共同基线 MS-00\"] --> B1[\"B：Context组件 MS-C1\"]",
              "  A0 --> C1[\"C：Tool组件 MS-T1\"]", "  A0 --> D1[\"D：Runner协议 MS-R1\"]",
              "  B1 --> I1[\"A：Context与Intent/Model接线 MS-I1\"]", "  I1 --> B2[\"B：快照与引用 MS-C2\"]",
              "  C1 --> I2[\"A：Tool/Runner公共接线 MS-I2\"]", "  D1 --> I2", "  I1 --> I2",
              "  I2 --> C2[\"C：调用/审批/效果账本 MS-T2\"]", "  I2 --> D2[\"D：实际配对；获准后进入执行 MS-R2\"]",
              "  B2 --> I3[\"A：汇合；按原P1轮次进入Agent闭环\"]", "  C2 --> I3", "  D2 --> I3", "```", "",
              "每次合入发布新集成SHA。开发session在包边界同步后进入下一包；未完成的分支不会直接作为另一个session的依赖。MS-I3仅是汇合入口，P1-06变更、P1-10真实界面等原工作包仍须另行完成。", "",
              "## 5. 开3个或5个怎样调整", "",
              "| 总session数 | 分配 | 调整 |", "| --- | --- | --- |",
              "| 3 | A集成＋B上下文＋C工具 | Runner协议放下一波，由已完成首包的开发session接手；先更新负责人及路径归属，不能默认多出第4个 |",
              "| **4，推荐** | A集成＋B上下文＋C工具＋D Runner | 符合3个session分别开发、另1个负责合并的想法 |",
              "| 5 | 上面4个＋E样本/评测 | E写独立样本与审阅标准，不再让第5个一起改共享基础文件 |", "",
              "首次尝试先跑完一波小包，再按实际冲突、等待与集成耗时决定是否增加session；不预估线性提速。", "",
              "## 6. 每个包的交付与正式状态", "", "| 包 | 负责 | 标题 | 组件开发前置 | 原轮 |", "| --- | --- | --- | --- | --- |"]
    for p in PACKAGES:
        lines.append(f"| {p['id']} | {p['session']} | {p['title']} | {'、'.join(p['deps']) or '现有进度收尾'} | " + "、".join(link(path, f"docs/plan/rounds/{r}.md", r) for r in p["rounds"]) + " |")
    lines += ["", "开发交付只写各自handoff；A在" + link(path, "docs/coordination/DISPATCH.md", "统一派发表") + "记录基线、派发与接受。两者是不同文件，减少状态记录冲突。组件交接通过不自动将整轮改为accepted。", "",
              "## 7. 具体入口", "",
              "- " + link(path, "docs/plan/PARALLEL_WORKFLOW.md", "文件归属、worktree、公共变更与合并流程") + "。",
              "- " + link(path, "docs/coordination/HANDOFF_TEMPLATE.md", "提交交接模板") + "与" + link(path, "docs/coordination/REQUEST_TEMPLATE.md", "公共接口变更模板") + "。",
              "- 各session页末尾有可复制到新聊天的开工说明。",
              "- " + link(path, "planning/parallel-plan.json", "机器分工/依赖/归属表") + "与" + link(path, "docs/plan/parallel-check.json", "计划检查结果") + "。",
              "- " + link(path, "planning/parallel_catalog.py", "并行计划维护源") + "；运行 `python planning/build_parallel.py`，总计划生成器也会重建本计划。", ""]
    write(path, "\n".join(lines))


def main():
    errors = validate()
    for key, session in SESSIONS.items():
        target = ROOT / session["report"]
        if not target.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(f"# Session {key}交接记录\n\n当前：未派发。基线SHA：待A完成MS-00后公布。\n\n负责：{session['name']}。首包：{'、'.join(session['starts'])}。\n\n本文件只由本session填写实际提交；A在[DISPATCH.md](../DISPATCH.md)记录派发与接受。模板见[HANDOFF_TEMPLATE.md](../HANDOFF_TEMPLATE.md)。\n\n## 实际提交\n\n- 所依据的真实基线SHA：待定。\n- 提交SHA/修改文件/验证证据：未开工。\n- 公共接口提案/接线需求：未提交。\n- 未通过项：待执行。\n", encoding="utf-8")
    build_sessions()
    build_overview()
    report = {"plan_version": VERSION, "date": DATE, "status": "first_wave_integrated", "baseline": BASELINE,
              "session_progress": SESSION_PROGRESS, "package_progress": PACKAGE_PROGRESS,
              "recommended_sessions": 4, "configurations": CONFIGURATIONS, "sessions": SESSIONS,
              "packages": PACKAGES, "full_round_dependencies_unchanged": True, "runtime_gates_unchanged": True}
    write("planning/parallel-plan.json", json.dumps(report, ensure_ascii=False, indent=2))
    (ROOT / "docs/plan/parallel-check.json").write_text("{}\n", encoding="utf-8")
    checked_links = 0
    for path in GENERATED + ["docs/plan/PARALLEL_WORKFLOW.md", "docs/coordination/HANDOFF_TEMPLATE.md", "docs/coordination/REQUEST_TEMPLATE.md", "docs/coordination/DISPATCH.md"] + [s["report"] for s in SESSIONS.values()]:
        target = ROOT / path
        if not target.is_file():
            errors.append(f"document missing: {path}")
            continue
        for href in re.findall(r"\]\(([^)]+)\)", target.read_text(encoding="utf-8")):
            if "://" in href or href.startswith("#"):
                continue
            destination = (target.parent / href.split("#", 1)[0]).resolve()
            # Worker fixture receipts are ignored local artifacts, not clone-time docs.
            if destination.is_relative_to(ROOT / "tests/.artifacts"):
                continue
            checked_links += 1
            if not destination.is_file():
                errors.append(f"broken link: {path}: {href}")
    check = {"date": DATE, "status": "passed" if not errors else "failed", "packages": len(PACKAGES),
             "session_templates": len(SESSIONS), "ownership_paths_disjoint": not any("ownership overlap" in e for e in errors),
             "package_dependencies_acyclic": not any("cycle" in e for e in errors),
             "local_links_checked": checked_links, "session_dispatch_ready": BASELINE["dispatch_ready"],
             "runtime_tests": "not_run_by_plan_generator", "git_operations": "not_performed", "errors": errors}
    write("docs/plan/parallel-check.json", json.dumps(check, ensure_ascii=False, indent=2))
    print(json.dumps(check, ensure_ascii=False))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
