from datetime import UTC, datetime, timedelta

from app.database.models import Item, Marketplace, MarketSnapshot
from app.database.repository import get_latest_states

T0 = datetime(2026, 11, 22, 10, 0, tzinfo=UTC)


def snapshot(item, marketplace, collected_at, price, listings):
    return MarketSnapshot(
        item_id=item.id,
        marketplace_id=marketplace.id,
        collected_at=collected_at,
        price_minor=price,
        currency="EUR",
        listings_count=listings,
        volume=None,
    )


def add_history(session):
    marketplace = Marketplace(code="test", name="Test")
    old_item = Item(market_hash_name="Sticker | Old")
    new_item = Item(market_hash_name="Sticker | New")
    session.add_all([marketplace, old_item, new_item])
    session.flush()
    session.add_all([
        snapshot(old_item, marketplace, T0, 200, 10),
        snapshot(old_item, marketplace, T0 + timedelta(hours=2), 250, 7),
        snapshot(new_item, marketplace, T0 + timedelta(hours=3), 999, 1),
    ])
    session.flush()
    return marketplace, old_item, new_item


def test_without_at_returns_current_state(session):
    marketplace, old_item, new_item = add_history(session)
    states = get_latest_states(session, marketplace.id)
    assert states == {old_item.id: (250, 7, "EUR"), new_item.id: (999, 1, "EUR")}


def test_state_at_past_moment(session):
    marketplace, old_item, _ = add_history(session)
    states = get_latest_states(session, marketplace.id, at=T0 + timedelta(hours=1))
    assert states == {old_item.id: (200, 10, "EUR")}


def test_snapshot_exactly_at_moment_is_included(session):
    marketplace, old_item, _ = add_history(session)
    states = get_latest_states(session, marketplace.id, at=T0 + timedelta(hours=2))
    assert states == {old_item.id: (250, 7, "EUR")}


def test_nothing_before_first_snapshot(session):
    marketplace, _, _ = add_history(session)
    states = get_latest_states(session, marketplace.id, at=T0 - timedelta(minutes=1))
    assert states == {}