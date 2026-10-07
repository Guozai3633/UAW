"""Compare requested sources with the complete Run-owned source set."""

from typing import Any

from uaw.intent.ports import InputReaderPort
from uaw.run.inputs import InputSet
from uaw.shared.contracts import TrustedExecutionContext
from uaw.shared.errors import CapabilityUnavailable, reject


class OriginalReader:
    def __init__(self, reader: InputReaderPort) -> None:
        self.reader = reader

    async def read(self, request: dict[str, Any], ctx: TrustedExecutionContext) -> InputSet:
        if request["material_refs"]:
            raise CapabilityUnavailable("intent_material_ingestion")
        inputs = await self.reader.read(ctx)
        if request["original_input_ref"] != inputs.refs[0] or request["user_patch_refs"] != list(
            inputs.refs[1:]
        ):
            raise reject(
                "intent_input_stale",
                "Request must contain the complete current user source set",
                412,
            )
        return inputs
