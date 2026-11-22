from datetime import UTC, datetime, timedelta
from decimal import Decimal

from app.analysis.window import compare_window
from app.database.models import CollectionRun, Item, Marketplace, MarketSnapshot

T0 = datetime(2026, 11, 22, 10, 0, tzinfo=UTC)
END = T0 + timedelta(hours=1)
WINDOW = timedelta(hours=1)


def at(minutes):
    return T0 + timedelta(minutes=minutes)


def add_snapshot(session, item, marketplace, minutes, price, listings, currency="EUR"):
    session.add(
        MarketSnapshot(
            item_id=item.id,
            marketplace_id=marketplace.id,
            collected_at=at(minutes),
            price_minor=price,
            currency=currency,
            listings_count=listings,
            volume=None,
        )
    )


def add_runs(session, marketplace, run_minutes):
    for minutes in run_minutes:
        session.add(
            CollectionRun(
                marketplace_id=marketplace.id,
                started_at=at(minutes),
                finished_at=at(minutes) + timedelta(seconds=10),
                status="success",
            )
        )


def build_report(session, run_minutes=range(0, 61, 5)):
    marketplace = Marketplace(code="test", name="Test")
    risen = Item(market_hash_name="Sticker | Risen")
    new = Item(market_hash_name="Sticker | New")
    switched = Item(market_hash_name="Sticker | Switched")
    session.add_all([marketplace, risen, new, switched])
    session.flush()

    add_snapshot(session, risen, marketplace, -10, 200, 10)
    add_snapshot(session, risen, marketplace, 30, 250, 7)
    add_snapshot(session, new, marketplace, 20, 999, 1)
    add_snapshot(session, switched, marketplace, -10, 100, 5)
    add_snapshot(session, switched, marketplace, 40, 120, 5, currency="USD")
    add_runs(session, marketplace, run_minutes)
    session.flush()

    report = compare_window(session, marketplace.id, END, WINDOW)
    by_id = {change.item_id: change for change in report.changes}
    return report, {
        "risen": by_id[risen.id],
        "new": by_id[new.id],
        "switched": by_id[switched.id],
    }


def test_price_and_listings_changes(session):
    _, changes = build_report(session)
    risen = changes["risen"]
    assert (risen.price_before, risen.price_now) == (200, 250)
    assert risen.price_change_percent == Decimal("25.00")
    assert risen.listings_change == -3


def test_item_that_appeared_in_window_has_unknown_change(session):
    _, changes = build_report(session)
    new = changes["new"]
    assert new.price_before is None
    assert new.price_change_percent is None
    assert new.listings_change is None


def test_currency_switch_gives_no_percent(session):
    _, changes = build_report(session)
    assert changes["switched"].price_change_percent is None


def test_regular_runs_make_window_complete(session):
    report, _ = build_report(session)
    assert report.gaps == []
    assert report.is_complete


def test_missing_runs_make_window_incomplete(session):
    report, _ = build_report(session, run_minutes=range(0, 21, 5))
    assert report.gaps == [(at(20), END)]
    assert not report.is_complete