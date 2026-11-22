from datetime import datetime, timedelta
from itertools import pairwise

Gap = tuple[datetime, datetime]


def find_gaps(
    run_times: list[datetime],
    start: datetime,
    end: datetime,
    max_gap: timedelta,
) -> list[Gap]:
    inside = sorted(t for t in run_times if start <= t <= end)
    points = [start, *inside, end]
    return [(a, b) for a, b in pairwise(points) if b - a > max_gap]