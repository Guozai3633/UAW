from uaw.shared.contracts import Failure
from uaw.shared.errors import DomainError


def fail(
    code: str, message: str, *, phase: str, category: str = "arguments", status: int = 422
) -> DomainError:
    return DomainError(
        Failure(code=code, category=category, message=message, retryable=False, failed_phase=phase),
        status_code=status,
    )
