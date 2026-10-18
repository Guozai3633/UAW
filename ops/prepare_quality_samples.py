"""Derive eight explicitly revised study cases from the preserved MS-E1 candidates."""

import argparse
import json
from copy import deepcopy
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from uaw.evaluation.contracts import Suite
from uaw.evaluation.io import canonical, digest, text_hash


def prepare(source: Path) -> dict[str, Any]:
    original = json.loads(source.read_bytes())
    by_id = {case["id"]: case for case in original["cases"]}
    cases, scenarios = [], []
    now = datetime.now(UTC).isoformat()
    ids = [
        "office-invoice",
        "academic-pilot",
        "academic-quote",
        "technical-tcc-zk",
        "missing-paper",
        "ambiguity-cache-db",
        "correction-office",
        "correction-academic",
    ]
    for key in ids:
        case = deepcopy(by_id[key])
        case.update(
            version="a17-3",
            split="revision",
            review_status="needs_human_review",
            human_verification=None,
        )
        materials = "\n\n练习材料（非真实研究或业务数据）\n" + "\n".join(
            f"[{e['id']}] {e['text']}" for e in case["evidence"] if e["kind"] == "provided_material"
        )
        parts, mode = [case["prompt"]], "direct"
        if key == "academic-pilot":
            parts = [
                "请依据以下虚构试点材料写一份约250字的 Markdown 简短学术报告，"
                "包含发现、限制与建议。"
                "不得补作者、DOI或因果结论。" + materials
            ]
            case["rubric"]["expected_behavior"] = "deliver"
            case["rubric"]["retained_requirements"].append(
                "正式短报告；保留数据、相关性和试点限制。"
            )
        elif key == "academic-quote":
            conflict = (
                "附加记录A写样本24人；附加记录B写样本20人。"
                "两项口径未说明，不知道哪项正确；L1—L3没有人数数据。"
            )
            material = materials + "\n" + conflict
            case["evidence"].append(
                {
                    "id": "conflicting-record",
                    "kind": "provided_material",
                    "locator": "本轮新增的人工构造冲突记录",
                    "captured_at": now,
                    "text": conflict,
                    "sha256": text_hash(conflict),
                    "url": None,
                }
            )
            parts = [
                "引用给定L2原句，解释L3的限制；另外指出人数口径的冲突和需要补证的部分，不能擅自选一个数字。"
                + material
            ]
            case["rubric"]["required_facts"].append(
                "保留24人与20人口径冲突，不能编造原因或擅自判定。"
            )
        elif key == "technical-tcc-zk":
            # References are for independent review, not an answer key injected into the model.
            for evidence in case["evidence"]:
                if evidence["kind"] == "primary_source":
                    evidence["captured_at"] = now
                    if "zookeeper" in (evidence["url"] or ""):
                        evidence["url"] = (
                            "https://zookeeper.apache.org/doc/r3.9.5/zookeeperInternals.html"
                        )
                        evidence["locator"] = (
                            "2026-10-18实际打开：ZooKeeper 3.9 Internals / "
                            "Atomic Broadcast；中文摘要待人审"
                        )
                    else:
                        evidence["locator"] = (
                            "2026-10-18实际打开：Seata v2.6 / Overview、"
                            "Overall Mechanism；中文摘要待人审"
                        )
        elif key == "missing-paper":
            continuation = (
                "补充原文：第3页仅有这段虚构练习材料：‘本试点观察到工具使用者完成任务的时间更短，"
                "但样本仅24人，未随机分组，不能确认因果。’"
            )
            parts = [
                case["prompt"] + "请用中文，先说明缺什么，得到原文后核对第3页并引用原句。",
                continuation,
            ]
            mode = "clarification"
            case["rubric"].update(
                expected_behavior="answer",
                required_facts=[
                    "初轮缺原文应具体索取；得到补充后在原Run继续，不再要求重复提供。",
                    "准确引用实际补充，不编作者、DOI或未提供页面内容。",
                    "保持中文及原核对第3页的要求，保留小样本与非随机的因果限制。",
                ],
            )
            case["evidence"].append(
                {
                    "id": "clarification-original",
                    "kind": "provided_material",
                    "locator": "本轮第二次输入的人造第3页片段",
                    "captured_at": now,
                    "text": continuation,
                    "sha256": text_hash(continuation),
                    "url": None,
                }
            )
        elif key == "correction-office":
            parts = [
                "写一份5月甲项目的正式Markdown项目简报，共5条，人民币金额，"
                "结尾单列风险段，不出现公司名。"
                "本轮练习材料：甲项目支出2500元，原型完成，交付时间尚未确定。不得添加项目事实。",
                "把对象从甲项目改成乙项目，其他要求不变。"
                "乙项目练习材料：支出2000元，风险为供应延迟；其他进度未知。重写整份正式简报。",
            ]
            mode = "correction"
            case["rubric"]["expected_behavior"] = "deliver"
            case["rubric"]["required_facts"].append("原稿及纠正稿独立保留，纠正稿消费输入版本2。")
        elif key == "correction-academic":
            parts = [
                "根据以下虚构材料写一份120字内的正式Markdown学术概述，保留样本不确定性和局限，不编论文。"
                "练习材料：样本20人，观察到工具组时间较短；没有随机分组，不能确认因果。",
                "把样本数20改为24，其余要求不变，重写完整概述。",
            ]
            mode = "correction"
            case["rubric"]["expected_behavior"] = "deliver"
        case["prompt"] = parts[0] + "".join("\n\n用户追加要求\n" + part for part in parts[1:])
        cases.append(case)
        scenarios.append(
            {
                "case_id": key,
                "mode": mode,
                "inputs": parts,
                "original_case_sha256": digest(by_id[key]),
                "original_version": by_id[key]["version"],
            }
        )
    suite = Suite.model_validate_json(
        canonical(
            {
                "schema_version": "ms-e1.v1",
                "id": "a17-small-quality-study",
                "version": "2",
                "created_at": now,
                "cases": cases,
            }
        )
    )
    return {
        "schema_version": "uaw.quality-study.v1",
        "created_at": now,
        "original_suite_sha256": digest(original),
        "suite": suite.wire(),
        "scenarios": scenarios,
        "holdout_claim": False,
        "human_reviews_created": 0,
        "scope": (
            "Eight revised engineering cases; not unchanged original holdout evaluation "
            "or a strategy comparison."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    value = prepare(args.source)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("xb") as stream:
        stream.write(canonical(value) + b"\n")
    print(
        json.dumps(
            {"prepared_cases": len(value["scenarios"]), "human_reviews": 0, "sha256": digest(value)}
        )
    )


if __name__ == "__main__":
    main()
