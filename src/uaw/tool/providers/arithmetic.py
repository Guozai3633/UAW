"""Bounded Decimal arithmetic; no expressions, scripts or ambient Decimal context."""

import re
from decimal import (
    Context,
    Decimal,
    DecimalException,
    DivisionByZero,
    Inexact,
    InvalidOperation,
    Overflow,
    Rounded,
    Underflow,
    localcontext,
)

from uaw.shared.contracts import JsonObject, Principal, Ref
from uaw.tool.providers.local import LocalExecutor, LocalVerifier, local_estimates, local_spec
from uaw.tool.receipt_store import ToolResponseStore

PRECISION = 34
MAX_OPERANDS = 32
MAX_DIGITS = 64
MAX_OPERAND_LENGTH = 67
MAX_ADJUSTED_EXPONENT = 128
OPERATIONS = ("add", "subtract", "multiply", "divide", "percent")
DECIMAL_TEXT = re.compile(r"-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?", re.ASCII)


def arithmetic_spec(provider_ref: Ref) -> JsonObject:
    inputs: JsonObject = {
        "type": "object",
        "properties": {
            "operation": {"type": "string", "enum": list(OPERATIONS)},
            "operands": {
                "type": "array",
                "minItems": 2,
                "maxItems": MAX_OPERANDS,
                "items": {"type": "string", "minLength": 1, "maxLength": MAX_OPERAND_LENGTH},
            },
        },
        "required": ["operation", "operands"],
        "additionalProperties": False,
    }
    outputs: JsonObject = {
        "type": "object",
        "properties": {
            "value": {"type": "string", "minLength": 1, "maxLength": 164},
            "precision": {"type": "integer", "const": PRECISION},
            "rounding": {"type": "string", "const": "ROUND_HALF_EVEN"},
            "rounded": {"type": "boolean"},
            "inexact": {"type": "boolean"},
        },
        "required": ["value", "precision", "rounding", "rounded", "inexact"],
        "additionalProperties": False,
    }
    return local_spec(
        "arithmetic.calculate",
        "Calculate supplied decimal operands",
        "arithmetic",
        provider_ref,
        inputs,
        outputs,
    )


def calculate(args: JsonObject) -> JsonObject:
    if type(args) is not dict or set(args) != {"operation", "operands"}:
        raise ValueError("Expected operation and operands only")
    operation, raw = args["operation"], args["operands"]
    if type(operation) is not str or operation not in OPERATIONS:
        raise ValueError("Unsupported arithmetic operation")
    if type(raw) is not list or not 2 <= len(raw) <= MAX_OPERANDS:
        raise ValueError("Expected 2..32 decimal strings")
    if operation in {"divide", "percent"} and len(raw) != 2:
        raise ValueError("Divide and percent require exactly two operands")
    operands = []
    for item in raw:
        if (
            type(item) is not str
            or len(item) > MAX_OPERAND_LENGTH
            or DECIMAL_TEXT.fullmatch(item) is None
            or sum(c in "0123456789" for c in item) > MAX_DIGITS
        ):
            raise ValueError("Expected bounded plain ASCII decimal strings without exponent")
        operands.append(Decimal(item))
    # Construct an independent Context: callers cannot change precision/rounding/traps.
    context = Context(
        prec=PRECISION,
        rounding="ROUND_HALF_EVEN",
        Emax=128,
        Emin=-128,
        traps=[InvalidOperation, DivisionByZero, Overflow],
    )
    try:
        with localcontext(context) as active:
            active.clear_flags()
            value = operands[0]
            for operand in operands[1:]:
                if operation == "add":
                    value += operand
                elif operation == "subtract":
                    value -= operand
                elif operation == "multiply":
                    value *= operand
                elif operation == "divide":
                    if operand.is_zero():
                        raise ValueError("Division by zero")
                    value /= operand
                else:
                    # percent(base, rate) = base * rate / 100, same fixed rounding.
                    value = value * operand / Decimal(100)
                if (
                    not value.is_finite()
                    or active.flags[Underflow]
                    or (not value.is_zero() and abs(value.adjusted()) > MAX_ADJUSTED_EXPONENT)
                ):
                    raise ValueError("Arithmetic result exceeds magnitude limits")
            return {
                "value": format(value, "f"),
                "precision": PRECISION,
                "rounding": "ROUND_HALF_EVEN",
                "rounded": active.flags[Rounded],
                "inexact": active.flags[Inexact],
            }
    except DecimalException as exc:
        raise ValueError("Arithmetic exceeds supported finite Decimal range") from exc


def arithmetic_estimates(currency: str = "USD") -> JsonObject:
    return local_estimates(currency)


class ArithmeticExecutor(LocalExecutor):
    def __init__(
        self, source: ToolResponseStore, *, provider: Principal, currency: str = "USD"
    ) -> None:
        super().__init__(
            source,
            provider=provider,
            currency=currency,
            factory=arithmetic_spec,
            calculate=calculate,
        )


class ArithmeticVerifier(LocalVerifier):
    def __init__(self, provider_ref: Ref) -> None:
        super().__init__(provider_ref, factory=arithmetic_spec, calculate=calculate)
