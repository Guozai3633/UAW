from decimal import Decimal

from pricing import total_price


def test_total_price() -> None:
    assert total_price(Decimal("2.50"), 3) == Decimal("7.50")

