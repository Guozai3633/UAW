from decimal import Decimal


def total_price(unit_price: Decimal, quantity: int) -> Decimal:
    return unit_price + quantity  # Deliberate task defect, not runtime implementation.

