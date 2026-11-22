from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal

from sqlalchemy.orm import Session

from app.analysis.changes import absolute_change, percent_change
from app.analysis.coverage import Gap, find_gaps
from app.database.repository import get_latest_states, get_successful_run_times

MAX_RUN_GAP = timedelta(minutes=15)


@dataclass(frozen=True)
class ItemChange:
    item_id: int
    price_before: int | None
    price_now: int | None
    price_change_percent: Decimal | None
    listings_before: int | None
    listings_now: int | None
    listings_change: int | None


@dataclass(frozen=True)
class WindowReport:
    start: datetime
    end: datetime
    gaps: list[Gap]
    changes: list[ItemChange]

    @property
    def is_complete(self) -> bool:
        return not self.gaps


def compare_window(
    session: Session,
    marketplace_id: int,
    end: datetime,
    window: timedelta,
    max_gap: timedelta = MAX_RUN_GAP,
) -> WindowReport:
    start = end - window
    before = get_latest_states(session, marketplace_id, at=start)
    now = get_latest_states(session, marketplace_id, at=end)

    changes = []
    for item_id, (price_now, listings_now, currency_now) in now.items():
        price_before, listings_before, currency_before = before.get(
            item_id, (None, None, None)
        )
        same_currency = currency_before == currency_now
        changes.append(
            ItemChange(
                item_id=item_id,
                price_before=price_before,
                price_now=price_now,
                price_change_percent=(
                    percent_change(price_before, price_now) if same_currency else None
                ),
                listings_before=listings_before,
                listings_now=listings_now,
                listings_change=absolute_change(listings_before, listings_now),
            )
        )

    run_times = get_successful_run_times(session, marketplace_id, start, end)
    gaps = find_gaps(run_times, start, end, max_gap)
    return WindowReport(start=start, end=end, gaps=gaps, changes=changes)