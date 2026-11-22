from datetime import UTC, datetime, timedelta

from app.analysis.coverage import find_gaps

START = datetime(2026, 11, 22, 12, 0, tzinfo=UTC)
END = START + timedelta(hours=1)
MAX_GAP = timedelta(minutes=15)


def minutes(*values: int) -> list[datetime]:
    return [START + timedelta(minutes=v) for v in values]


def test_no_gaps_when_runs_are_regular():
    assert find_gaps(minutes(5, 15, 25, 35, 45, 55), START, END, MAX_GAP) == []


def test_gap_in_the_middle():
    runs = minutes(5, 10, 40, 50)
    assert find_gaps(runs, START, END, MAX_GAP) == [(runs[1], runs[2])]


def test_gap_at_the_start_and_end():
    runs = minutes(30, 40)
    assert find_gaps(runs, START, END, MAX_GAP) == [
        (START, runs[0]),
        (runs[1], END),
    ]


def test_whole_window_is_a_gap_without_runs():
    assert find_gaps([], START, END, MAX_GAP) == [(START, END)]


def test_runs_outside_the_window_are_ignored():
    runs = [START - timedelta(minutes=5), END + timedelta(minutes=5)]
    assert find_gaps(runs, START, END, MAX_GAP) == [(START, END)]


def test_order_of_runs_does_not_matter():
    assert find_gaps(minutes(55, 5, 35, 15, 45, 25), START, END, MAX_GAP) == []


def test_gap_exactly_max_gap_is_allowed():
    assert find_gaps(minutes(15, 30, 45), START, END, MAX_GAP) == []