"""Counts come from all attempts; quality comes only from supplied bound review."""

from collections import defaultdict
from datetime import datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal
from typing import Literal

from uaw.evaluation.contracts import Cost, Observation, Quantity, Rate


def utc(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def milliseconds(start: str, end: str) -> int:
    return (utc(end) - utc(start)) // timedelta(milliseconds=1)


def decimal_text(value: Decimal) -> str:
    return (
        format(value, "f").rstrip("0").rstrip(".")
        if "." in format(value, "f")
        else format(value, "f")
    )


def rate(numerator: int, denominator: int, *, provisional: bool = False) -> Rate:
    status: Literal["measured", "provisional", "not_applicable"] = (
        "not_applicable" if denominator == 0 else "provisional" if provisional else "measured"
    )
    return Rate(
        numerator=numerator,
        denominator=denominator,
        value=None
        if denominator == 0
        else decimal_text(
            (Decimal(numerator) / denominator).quantize(
                Decimal("0.00000001"), rounding=ROUND_HALF_UP
            )
        ),
        status=status,
    )


def quantity(rows: tuple[Observation, ...], name: str) -> Quantity:
    values = [getattr(row.usage, name) for row in rows]
    return Quantity(
        known_total=sum(v for v in values if v is not None),
        unknown_attempts=sum(v is None for v in values),
    )


def costs(rows: tuple[Observation, ...], acceptable: int) -> tuple[Cost, ...]:
    currencies: dict[str, list[Observation]] = defaultdict(list)
    for row in rows:
        currencies[row.usage.currency].append(row)
    result = []
    for currency, group in sorted(currencies.items()):
        totals = {
            state: sum(
                (
                    Decimal(r.usage.money)
                    for r in group
                    if r.usage.billing_state == state and r.usage.money is not None
                ),
                Decimal(0),
            )
            for state in ("confirmed", "pending", "unknown")
        }
        complete = all(
            r.usage.billing_state == "confirmed" and r.usage.money is not None for r in group
        )
        result.append(
            Cost(
                currency=currency,
                confirmed=decimal_text(totals["confirmed"]),
                pending=decimal_text(totals["pending"]),
                unknown_estimate=decimal_text(totals["unknown"]),
                unknown_money_attempts=sum(r.usage.money is None for r in group),
                pending_attempts=sum(r.usage.billing_state == "pending" for r in group),
                unknown_billing_attempts=sum(r.usage.billing_state == "unknown" for r in group),
                confirmed_per_acceptable_output=decimal_text(
                    (totals["confirmed"] / acceptable).quantize(
                        Decimal("0.00000001"), rounding=ROUND_HALF_UP
                    )
                )
                if acceptable and complete
                else None,
            )
        )
    return tuple(result)
