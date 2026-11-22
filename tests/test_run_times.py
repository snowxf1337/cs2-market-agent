from datetime import UTC, datetime, timedelta

from app.database.models import CollectionRun, Marketplace
from app.database.repository import get_successful_run_times

T0 = datetime(2026, 11, 22, 10, 0, tzinfo=UTC)


def make_marketplace(session, code="test"):
    marketplace = Marketplace(code=code, name=code.title())
    session.add(marketplace)
    session.flush()
    return marketplace


def add_run(session, marketplace, minutes, status="success"):
    started_at = T0 + timedelta(minutes=minutes)
    session.add(
        CollectionRun(
            marketplace_id=marketplace.id,
            started_at=started_at,
            finished_at=started_at + timedelta(seconds=10),
            status=status,
        )
    )
    return started_at


def test_returns_only_successful_runs_in_order(session):
    marketplace = make_marketplace(session)
    late = add_run(session, marketplace, 10)
    add_run(session, marketplace, 5, status="failed")
    early = add_run(session, marketplace, 0)
    add_run(session, marketplace, 15, status="rate_limited")

    result = get_successful_run_times(session, marketplace.id, T0, T0 + timedelta(hours=1))
    assert result == [early, late]


def test_window_bounds_are_inclusive(session):
    marketplace = make_marketplace(session)
    add_run(session, marketplace, -5)
    start = add_run(session, marketplace, 0)
    end = add_run(session, marketplace, 60)
    add_run(session, marketplace, 65)

    result = get_successful_run_times(session, marketplace.id, start, end)
    assert result == [start, end]


def test_ignores_other_marketplaces(session):
    ours = make_marketplace(session, "ours")
    other = make_marketplace(session, "other")
    mine = add_run(session, ours, 0)
    add_run(session, other, 5)

    result = get_successful_run_times(session, ours.id, T0, T0 + timedelta(hours=1))
    assert result == [mine]