from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select

from app.database.models import Item, Marketplace, MarketSnapshot
from app.database.repository import get_or_create_marketplace, save_snapshots
from app.market import MarketItem

FIRST_RUN = datetime(2026, 11, 22, 12, 0, tzinfo=UTC)
SECOND_RUN = FIRST_RUN + timedelta(minutes=5)
REDLINE = "AK-47 | Redline (Field-Tested)"
DOPPLER = "Glock-18 | Gamma Doppler (Factory New)"


def make_item(name=REDLINE, price=1250, quantity=40, version=None):
    return MarketItem(
        market_hash_name=name,
        version=version,
        category="rifle",
        currency="EUR",
        min_price_minor=price,
        quantity=quantity,
    )


def count(session, model):
    return session.scalar(select(func.count()).select_from(model))


def skinport(session):
    return get_or_create_marketplace(session, "skinport", "Skinport")


def test_get_or_create_marketplace_is_idempotent(session):
    first = skinport(session)
    second = skinport(session)

    assert first.id == second.id
    assert count(session, Marketplace) == 1


def test_first_save_writes_all_items(session):
    items = [make_item(), make_item(name="AWP | Asiimov (Field-Tested)")]
    written = save_snapshots(session, skinport(session), items, FIRST_RUN)

    assert written == 2
    assert count(session, Item) == 2
    assert count(session, MarketSnapshot) == 2


def test_unchanged_items_are_not_written_again(session):
    marketplace = skinport(session)
    save_snapshots(session, marketplace, [make_item()], FIRST_RUN)

    written = save_snapshots(session, marketplace, [make_item()], SECOND_RUN)

    assert written == 0
    assert count(session, MarketSnapshot) == 1


def test_price_change_is_written(session):
    marketplace = skinport(session)
    save_snapshots(session, marketplace, [make_item(price=1250)], FIRST_RUN)

    written = save_snapshots(session, marketplace, [make_item(price=1300)], SECOND_RUN)

    assert written == 1
    assert count(session, MarketSnapshot) == 2


def test_quantity_change_is_written(session):
    marketplace = skinport(session)
    save_snapshots(session, marketplace, [make_item(quantity=40)], FIRST_RUN)

    written = save_snapshots(session, marketplace, [make_item(quantity=12)], SECOND_RUN)

    assert written == 1


def test_snapshot_fields_are_stored(session):
    save_snapshots(session, skinport(session), [make_item()], FIRST_RUN)
    session.expire_all()

    snapshot = session.scalars(select(MarketSnapshot)).one()
    assert snapshot.collected_at == FIRST_RUN
    assert snapshot.price_minor == 1250
    assert snapshot.listings_count == 40
    assert snapshot.currency == "EUR"
    assert snapshot.volume is None


def test_out_of_stock_item_is_stored_with_null_price(session):
    save_snapshots(session, skinport(session), [make_item(price=None, quantity=0)], FIRST_RUN)
    session.expire_all()

    snapshot = session.scalars(select(MarketSnapshot)).one()
    assert snapshot.price_minor is None
    assert snapshot.listings_count == 0


def test_duplicate_input_items_are_saved_once(session):
    written = save_snapshots(session, skinport(session), [make_item(), make_item()], FIRST_RUN)

    assert written == 1
    assert count(session, MarketSnapshot) == 1


def test_item_versions_are_stored_as_separate_items(session):
    items = [
        make_item(name=DOPPLER, version="Phase 1"),
        make_item(name=DOPPLER, version="Emerald"),
    ]
    save_snapshots(session, skinport(session), items, FIRST_RUN)

    assert count(session, Item) == 2