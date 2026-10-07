"""Only fixed, content-free request failure fields enter control-plane logs."""

import structlog


def report_request_failure(operation: str, error_type: str) -> None:
    structlog.get_logger("uaw.control_plane").error(
        "request_failed", operation=operation, error_type=error_type
    )
