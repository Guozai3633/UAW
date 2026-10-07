"""Cross-module ports, no provider calls or source writes inside Intent."""

from typing import Any, Protocol

from uaw.run.inputs import InputSet
from uaw.shared.contracts import TrustedExecutionContext


class InputReaderPort(Protocol):
    async def read(self, ctx: TrustedExecutionContext) -> InputSet: ...


class UnderstandingContextPort(Protocol):
    async def prepare(
        self, inputs: InputSet, ctx: TrustedExecutionContext, output_reserve: int
    ) -> dict[str, Any]: ...
