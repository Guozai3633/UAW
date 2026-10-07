"""Deterministic transition constraints; semantic completion has a separate owner."""

from uaw.shared.errors import reject

RUN_TRANSITIONS = {
    "queued": {"preparing", "cancelled"},
    "preparing": {"running", "waiting_for_user"},
    "running": {"verifying", "waiting_for_user", "waiting_for_merge"},
    "verifying": {"running", "waiting_for_user", "waiting_for_merge"},
    "waiting_for_user": {"preparing", "running", "verifying"},
    "waiting_for_merge": {"running", "verifying"},
    "completed": set(),
    "failed": set(),
    "cancelled": set(),
}
ITEM_TRANSITIONS = {
    "pending": {"in_progress", "waiting", "cancelled"},
    "in_progress": {"waiting", "completed", "failed", "cancelled"},
    "waiting": {"in_progress", "completed", "failed", "declined", "cancelled"},
    "completed": set(),
    "failed": set(),
    "declined": set(),
    "cancelled": set(),
}


def validate_transition(current: str, target: str, *, item: bool = False) -> None:
    transitions = ITEM_TRANSITIONS if item else RUN_TRANSITIONS
    if target not in transitions.get(current, set()):
        raise reject("state_transition_denied", "State transition is not allowed", 409, "conflict")


def validate_worker_transition(current: str, target: str) -> None:
    if target in ("completed", "failed", "cancelled"):
        raise reject(
            "completion_controller_required",
            "Worker cannot submit terminal task state",
            403,
            "policy",
        )
    validate_transition(current, target)
