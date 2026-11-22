from decimal import Decimal

import pytest

from app.analysis.changes import absolute_change, percent_change


@pytest.mark.parametrize(
    ("previous", "current", "expected"),
    [
        (200, 250, Decimal("25.00")),
        (250, 200, Decimal("-20.00")),
        (300, 200, Decimal("-33.33")),
        (300, 400, Decimal("33.33")),
        (278, 278, Decimal("0.00")),
    ],
)
def test_percent_change(previous, current, expected):
    assert percent_change(previous, current) == expected


@pytest.mark.parametrize(
    ("previous", "current"),
    [
        (None, 250),
        (250, None),
        (None, None),
        (0, 5),
    ],
)
def test_percent_change_is_unknown_when_it_cannot_be_calculated(previous, current):
    assert percent_change(previous, current) is None


def test_absolute_change_works_from_zero():
    assert absolute_change(0, 5) == 5


def test_absolute_change_is_unknown_without_both_values():
    assert absolute_change(None, 5) is None