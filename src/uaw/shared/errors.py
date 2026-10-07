from typing import Any

from uaw.shared.contracts import Failure


class DomainError(Exception):
    def __init__(self, failure: Failure, status_code: int = 422) -> None:
        self.failure = failure
        self.status_code = status_code
        super().__init__(failure.message)


class CapabilityUnavailable(DomainError):
    def __init__(self, capability: str) -> None:
        super().__init__(
            Failure(
                code="capability_unavailable",
                category="dependency",
                message=f"Capability is not implemented: {capability}",
                retryable=False,
                failed_phase="admission",
            ),
            status_code=503,
        )


def error_result(exc: DomainError) -> dict[str, Any]:
    kind = {
        401: "denied",
        403: "denied",
        404: "missing",
        409: "conflict",
        410: "stale",
        412: "stale",
    }.get(exc.status_code, "failed")
    if exc.failure.category == "cancelled":
        kind = "cancelled"
    return {"kind": kind, "failure": exc.failure.wire(), "output_refs": []}


def reject(code: str, message: str, status: int = 422, category: str = "validation") -> DomainError:
    category = {"validation": "arguments", "permission": "authorization"}.get(category, category)
    return DomainError(
        Failure(
            code=code, category=category, message=message, retryable=False, failed_phase="admission"
        ),
        status_code=status,
    )
