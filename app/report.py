import argparse
from datetime import timedelta
from decimal import Decimal

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.analysis.window import compare_window
from app.collectors.collector import utc_now
from app.config import Settings
from app.database.models import Item, Marketplace


def euros(minor: int | None) -> str:
    return "-" if minor is None else f"{Decimal(minor) / 100:.2f}"


def main() -> None:
    parser = argparse.ArgumentParser(description="Show price changes over a time window")
    parser.add_argument("--hours", type=float, default=1)
    parser.add_argument("--top", type=int, default=10)
    args = parser.parse_args()

    engine = create_engine(Settings().database_url())
    with Session(engine) as session:
        marketplace = session.scalars(
            select(Marketplace).where(Marketplace.code == "skinport")
        ).one()
        report = compare_window(session, marketplace.id, utc_now(), timedelta(hours=args.hours))
        names = dict(session.execute(select(Item.id, Item.market_hash_name)).all())

    print(f"Window: {report.start.astimezone():%H:%M} -> {report.end.astimezone():%H:%M}")
    if report.is_complete:
        print("Coverage: complete")
    else:
        print("Coverage: INCOMPLETE, gaps:")
        for gap_start, gap_end in report.gaps:
            print(f"  {gap_start.astimezone():%H:%M} -> {gap_end.astimezone():%H:%M}")

    moved = [c for c in report.changes if c.price_change_percent not in (None, 0)]
    moved.sort(key=lambda c: abs(c.price_change_percent), reverse=True)
    print(f"Items compared: {len(report.changes)}, price changed: {len(moved)}")
    for c in moved[: args.top]:
        print(
            f"{c.price_change_percent:+8}%  {euros(c.price_before):>8} -> {euros(c.price_now):>8}"
            f"  lots {c.listings_before}->{c.listings_now}  {names[c.item_id]}"
        )


if __name__ == "__main__":
    main()