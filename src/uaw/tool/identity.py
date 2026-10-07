"""Process-local action identity guard, never a durable execution ledger.

Attempts are transport metadata; identity binds tool/arguments/scope/model version.
No TTL eviction: at capacity admission fails rather than forgetting deduplication.
"""

from threading import RLock
from typing import Any

from uaw.shared.contracts import TrustedExecutionContext
from uaw.shared.schema import validate_contract
from uaw.tool.errors import fail
from uaw.tool.schema import digest


class ActionIdentities:
    def __init__(self, *, capacity: int = 4096) -> None:
        if type(capacity) is not int or not 1 <= capacity <= 65536:
            raise ValueError("Invalid action identity capacity")
        self.capacity = capacity
        self._bindings: dict[tuple[str, str, str], str] = {}
        self._lock = RLock()

    def bind(self, call: dict[str, Any], ctx: TrustedExecutionContext) -> bool:
        """Return True for an identical duplicate, reject reuse with different inputs."""
        if not ctx.run_id:
            raise fail(
                "dependency_unavailable",
                "Action identities require a trusted Run",
                phase="identity",
                category="dependency",
                status=503,
            )
        key = (ctx.principal.id, ctx.run_id, call["action_id"])
        fingerprint = digest(
            {
                "call": call,
                "scope": ctx.scope.wire(),
                "agent_id": ctx.agent_id,
                "task_id": ctx.task_id,
                "node_id": ctx.node_id,
                "capability_policy_ref": ctx.capability_policy_ref.wire(),
                "model_policy_ref": (ctx.model_policy_ref.wire() if ctx.model_policy_ref else None),
            }
        )
        with self._lock:
            previous = self._bindings.get(key)
            if previous is not None:
                if previous != fingerprint:
                    raise fail(
                        "action_conflict",
                        "Action ID was reused with different parameters",
                        phase="identity",
                        category="conflict",
                        status=409,
                    )
                return True
            if len(self._bindings) >= self.capacity:
                raise fail(
                    "identity_capacity",
                    "Action identity guard is full",
                    phase="identity",
                    category="dependency",
                    status=503,
                )
            self._bindings[key] = fingerprint
            return False


def require_safe_recovery(effect: str, effect_state: str) -> None:
    """Unknown write outcomes require reconciliation, irrespective of attempt ID."""
    validate_contract("EffectKind", effect)
    validate_contract("EffectState", effect_state)
    if effect != "read" and effect_state in {"pending", "unknown", "confirmed"}:
        raise fail(
            "unknown_effect" if effect_state != "confirmed" else "action_already_effective",
            "Write effect must be reconciled before a new attempt",
            phase="recovery",
            category="unknown_effect",
            status=409,
        )
