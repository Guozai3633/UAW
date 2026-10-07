"""Model Runtime public entry point; it never completes an Agent task or executes tools."""

from uaw.model.gateway import ModelGateway
from uaw.shared.contracts import JsonObject, TrustedExecutionContext
from uaw.shared.errors import DomainError, error_result, reject
from uaw.shared.schema import ContractViolation, validate_contract


class ModelFacade:
    def __init__(self, gateway: ModelGateway) -> None:
        self.gateway = gateway

    async def generate(self, request: JsonObject, ctx: TrustedExecutionContext) -> JsonObject:
        try:
            result = await self.gateway.generate(request, ctx)
        except ContractViolation:
            result = error_result(
                reject("model_request_invalid", "Model request does not match its contract")
            )
        except DomainError as exc:
            result = error_result(exc)
        validate_contract("RuntimeModelruntimeGenerateResult", result)
        return result

    async def close(self) -> None:
        await self.gateway.close()
