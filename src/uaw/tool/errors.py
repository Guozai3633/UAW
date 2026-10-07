from uaw.shared.contracts import Failure
from uaw.shared.errors import DomainError


def fail(
    code: str, message: str, *, phase: str, category: str = "arguments", status: int = 422
) -> DomainError:
    return DomainError(
        Failure(code=code, category=category, message=message, retryable=False, failed_phase=phase),
        status_code=status,
    )


def validate_dependency(name: str, response: object, phase: str) -> None:
    from uaw.shared.schema import ContractViolation, validate_contract

    try:
        validate_contract(name, response)
    except ContractViolation as exc:
        raise fail(
            "dependency_protocol_invalid",
            "Dependency returned an invalid named DTO",
            phase=phase,
            category="dependency",
            status=503,
        ) from exc
