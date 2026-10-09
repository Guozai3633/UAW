"""Read the actual bounded text/reference evidence, without network or shell claims."""

import re
from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from uaw.agent.contracts import Payload
from uaw.context.contracts import Reading
from uaw.model.evaluation_inputs import EvaluationSource
from uaw.shared.contracts import Ref, TrustedExecutionContext
from uaw.shared.errors import reject

EvidenceRead = Callable[[Ref, TrustedExecutionContext], Awaitable[Reading]]


def checked_reading(pin: Ref, reading: Reading) -> None:
    if (
        not isinstance(reading, Reading)
        or reading.ref != pin
        or not isinstance(reading.text, str)
        or len(reading.text.encode("utf-8")) > 65536
    ):
        raise reject("completion_reading_changed", "Exact bounded evidence reading required", 412)


@dataclass(frozen=True)
class CompletionEvidence:
    data: Payload
    offered: dict[str, Ref]
    pins: tuple[EvaluationSource, ...]
    checks: tuple[Payload, ...]


def check(
    identifier: str,
    kind: str,
    state: str,
    target: Ref,
    evidence: tuple[Ref, ...],
    summary: str,
    requirements: tuple[str, ...] = (),
) -> Payload:
    return {
        "id": identifier,
        "kind": kind,
        "state": state,
        "requirement_ids": list(requirements),
        "target_refs": [target.wire()],
        "evidence_refs": [r.wire() for r in evidence],
        "summary": summary,
    }


def external_links(text: str) -> tuple[str, ...]:
    # This detects unresolved links; it never substitutes parsing for semantic review.
    return tuple(dict.fromkeys(re.findall(r"https?://[^\s<>\)\]]+", text)))
