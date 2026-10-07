"""Bounded proposals with exact source coordinates; summaries never replace user goals."""

import hashlib
from copy import deepcopy
from typing import Any

from uaw.infrastructure.db.records import parameter_hash
from uaw.run.inputs import InputSet
from uaw.shared.errors import reject
from uaw.shared.schema import contract_schema, validate_contract

Payload = dict[str, Any]


def proposal_schema() -> Payload:
    definitions = contract_schema()["$defs"]

    def expand(node: Any) -> Any:
        if isinstance(node, list):
            return [expand(value) for value in node]
        if not isinstance(node, dict):
            return node
        if "$ref" in node:
            return expand(deepcopy(definitions[node["$ref"].rsplit("/", 1)[-1]]))
        return {key: expand(value) for key, value in node.items() if not key.startswith("x-")}

    result: Payload = expand(deepcopy(definitions["IntentProposal"]))
    return result


def located_source(quote: Payload, inputs: InputSet) -> Payload:
    index, start, end = quote["source_index"], quote["start"], quote["end"]
    if index >= len(inputs.inputs) or not 0 <= start < end <= len(inputs.inputs[index]["text"]):
        raise reject("intent_quote_invalid", "Source coordinate is outside the user input")
    if inputs.inputs[index]["text"][start:end] != quote["text"]:
        raise reject("intent_quote_invalid", "Quoted requirement differs from its user source")
    return {**inputs.refs[index], "location": {"kind": "text_span", "start": start, "end": end}}


def frame_candidate(proposal: Payload, inputs: InputSet, semantic_ref: Payload) -> Payload:
    validate_contract("IntentProposal", proposal)
    constraints: list[Payload] = []
    outputs: list[Payload] = []
    for value in proposal["requirements"]:
        quote = value["quote"]
        source = located_source(quote, inputs)
        identity = hashlib.sha256(parameter_hash({"quote": quote}).encode()).hexdigest()
        item = {
            "id": "requirement-" + identity,
            "text": quote["text"],
            "mandatory": True,
            "source_refs": [source],
        }
        if item not in constraints:
            constraints.append(item)
    for value in proposal["outputs"]:
        quote = value["quote"]
        located_source(quote, inputs)
        item = {
            "id": "output-" + parameter_hash(value),
            "kind": value["kind"],
            "description": quote["text"],
            "required": True,
        }
        if item not in outputs:
            outputs.append(item)
    # The executable goal retains all original words. Semantic paraphrase is advisory only.
    goal = inputs.inputs[0]["text"]
    for value in inputs.inputs[1:]:
        goal += "\n\n用户追加要求：\n" + value["text"]
    return {
        "task_id": inputs.run["task_id"],
        "original_input_ref": inputs.refs[0],
        "patch_refs": list(inputs.refs[1:]),
        "goal": goal,
        "summary": proposal["summary"],
        "constraints": constraints,
        "output_specs": outputs,
        "assumptions": proposal["assumptions"],
        "unresolved": proposal["unresolved"],
        "evidence_refs": [],
        "input_revision": inputs.state["revision"],
        "semantic_parse_ref": semantic_ref,
    }
