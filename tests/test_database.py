from datetime import UTC, datetime

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.database.models import Item, Marketplace, MarketSnapshot

COLLECTED_AT = datetime(2026, 11, 20, 12, 0, tzinfo=UTC)

DOPPLER = "★ Karambit | Doppler (Factory New)"

def add_item_and_marketplace(session):
    marketplace = Marketplace(code="test_market", name="Test Market")
    item = Item(market_hash_name="AK-47 | Redline (Field-Tested)")
    session.add_all([marketplace, item])
    session.flush()
    return item, marketplace


def make_snapshot(item, marketplace, **overrides):
    values = {
        "item_id": item.id,
        "marketplace_id": marketplace.id,
        "collected_at": COLLECTED_AT,
        "price_minor": 1250,
        "currency": "USD",
        "listings_count": 40,
        "volume": None,
    }
    values.update(overrides)
    return MarketSnapshot(**values)


def test_snapshot_is_saved_and_read_back(session):
    item, marketplace = add_item_and_marketplace(session)
    session.add(make_snapshot(item, marketplace))
    session.flush()
    session.expire_all()

    saved = session.scalars(select(MarketSnapshot)).one()
    assert saved.price_minor == 1250
    assert saved.currency == "USD"
    assert saved.volume is None
    assert saved.collected_at == COLLECTED_AT


def test_duplicate_snapshot_is_rejected(session):
    item, marketplace = add_item_and_marketplace(session)
    session.add(make_snapshot(item, marketplace))
    session.flush()

    session.add(make_snapshot(item, marketplace))
    with pytest.raises(IntegrityError):
        session.flush()


def test_negative_price_is_rejected(session):
    item, marketplace = add_item_and_marketplace(session)
    session.add(make_snapshot(item, marketplace, price_minor=-1))
    with pytest.raises(IntegrityError):
        session.flush()


def test_snapshot_for_unknown_item_is_rejected(session):
    item, marketplace = add_item_and_marketplace(session)
    session.add(make_snapshot(item, marketplace, item_id=999_999))
    with pytest.raises(IntegrityError):
        session.flush()


def test_duplicate_item_name_is_rejected(session):
    add_item_and_marketplace(session)
    session.add(Item(market_hash_name="AK-47 | Redline (Field-Tested)"))
    with pytest.raises(IntegrityError):
        session.flush()


def test_same_item_with_different_versions_is_allowed(session):
    session.add_all([
        Item(market_hash_name=DOPPLER, version="Phase 1"),
        Item(market_hash_name=DOPPLER, version="Ruby"),
    ])
    session.flush()


def test_duplicate_item_with_same_version_is_rejected(session):
    session.add(Item(market_hash_name=DOPPLER, version="Ruby"))
    session.flush()

    session.add(Item(market_hash_name=DOPPLER, version="Ruby"))
    with pytest.raises(IntegrityError):
        session.flush()