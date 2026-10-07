"""Provider-private types. Public wire objects still use the authoritative JSON Schema."""

from dataclasses import dataclass
from typing import Any

from pydantic import SecretStr

from uaw.shared.contracts import Failure
from uaw.shared.errors import DomainError

Payload = dict[str, Any]


@dataclass(frozen=True)
class ModelPrompt:
    messages: tuple[Payload, ...]
    tools: tuple[Payload, ...]
    estimated_tokens: int


@dataclass(frozen=True)
class ProviderRequest:
    endpoint: str
    credential: SecretStr | None
    settings: Payload
    config: Payload
    prompt: ModelPrompt
    protocol: str
    output_schema: Payload | None
    operation_id: str


@dataclass(frozen=True)
class ProviderResponse:
    text: str
    tool_calls: tuple[Payload, ...]
    finish_reason: str
    model_name: str
    resources: Payload
    raw: bytes
    structured_data: Payload | None = None
    cached_input_tokens: int | None = None
    receipt_id: str | None = None


class ProviderFailure(DomainError):
    def __init__(self, code: str, *, safe_retry: bool = False, category: str = "model_protocol"):
        self.safe_retry = safe_retry
        self.resources: Payload = {}
        self.response_raw: bytes | None = None
        super().__init__(
            Failure(
                code=code,
                category=category,
                message="Model attempt failed; inspect its protected receipt for status",
                retryable=safe_retry,
                failed_phase="model_provider",
                side_effect_state="unknown",
            ),
            502,
        )
