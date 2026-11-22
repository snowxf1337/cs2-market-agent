from decimal import ROUND_HALF_UP, Decimal


def percent_change(previous: int | None, current: int | None) -> Decimal | None:
    if previous is None or current is None or previous == 0:
        return None
    change = Decimal(current - previous) / Decimal(previous) * 100
    return change.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def absolute_change(previous: int | None, current: int | None) -> int | None:
    if previous is None or current is None:
        return None
    return current - previous