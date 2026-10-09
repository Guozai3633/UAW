"""Completion contracts come from the owned TaskFrame, never a new model goal."""

from uaw.agent.contracts import Payload
from uaw.shared.schema import validate_contract


def contract_from_frame(frame: Payload, *, acceptance_required: bool = False) -> Payload:
    validate_contract("TaskFrame", frame)
    original = {
        "id": "original-request",
        "text": frame["goal"],
        "mandatory": True,
        "source_refs": [frame["original_input_ref"], *frame["patch_refs"]],
        "evidence_kinds": ["semantic"],
    }
    requirements = [original, *frame["constraints"]]
    for output in frame["output_specs"]:
        requirements.append(
            {
                "id": "output-" + output["id"],
                "text": "Requested output: " + output["kind"] + ". " + output["description"],
                "mandatory": output["required"],
                "source_refs": original["source_refs"],
                "evidence_kinds": ["semantic"],
            }
        )
    if len(requirements) > 128 or len({r["id"] for r in requirements}) != len(requirements):
        raise ValueError("Duplicate or excessive TaskFrame requirements")
    value = {
        "goal": frame["goal"],
        "requirements": requirements,
        "outputs": frame["output_specs"],
        "version": str(frame["revision"]),
        "acceptance_required": acceptance_required,
    }
    validate_contract("Contract", value)
    return value


def report_outcome(contract: Payload, report: Payload) -> str:
    validate_contract("Contract", contract)
    validate_contract("VerificationReport", report)
    verdicts = report["verdicts"]
    expected = {r["id"] for r in contract["requirements"]}
    if len(verdicts) != len(expected) or {v["requirement_id"] for v in verdicts} != expected:
        return "blocked"
    states = [
        v["state"]
        for v in verdicts
        if any(r["id"] == v["requirement_id"] and r["mandatory"] for r in contract["requirements"])
    ]
    states += [c["state"] for c in report["checks"]]
    if "failed" in states:
        return "failed"
    if not states or any(s != "passed" for s in states):
        return "blocked"
    return "succeeded"
