from datetime import datetime

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import distinct_on
from sqlalchemy.orm import Session

from app.database.models import Item, Marketplace, MarketSnapshot
from app.market import MarketItem


ItemKey = tuple[str, str | None]


def get_or_create_marketplace(session: Session, code: str, name: str) -> Marketplace:
    marketplace = session.scalars(
        select(Marketplace).where(Marketplace.code == code)
    ).one_or_none()
    if marketplace is None:
        marketplace = Marketplace(code=code, name=name)
        session.add(marketplace)
        session.flush()
    return marketplace


def get_item_ids(session: Session, keys: set[ItemKey]) -> dict[ItemKey, int]:
    rows = session.execute(select(Item.id, Item.market_hash_name, Item.version))
    item_ids = {(row.market_hash_name, row.version): row.id for row in rows}

    new_items = [
        Item(market_hash_name=name, version=version)
        for name, version in keys - item_ids.keys()
    ]
    session.add_all(new_items)
    session.flush()
    item_ids.update({(item.market_hash_name, item.version): item.id for item in new_items})
    return item_ids


def get_latest_states(session: Session, marketplace_id: int) -> dict[int, tuple]:
    statement = (
        select(
            MarketSnapshot.item_id,
            MarketSnapshot.price_minor,
            MarketSnapshot.listings_count,
            MarketSnapshot.currency,
        )
        .where(MarketSnapshot.marketplace_id == marketplace_id)
        .order_by(MarketSnapshot.item_id, MarketSnapshot.collected_at.desc())
        .ext(distinct_on(MarketSnapshot.item_id))
    )
    return {
        row.item_id: (row.price_minor, row.listings_count, row.currency)
        for row in session.execute(statement)
    }


def save_snapshots(
    session: Session,
    marketplace: Marketplace,
    items: list[MarketItem],
    collected_at: datetime,
) -> int:
    unique_items: dict[ItemKey, MarketItem] = {}
    for item in items:
        unique_items.setdefault((item.market_hash_name, item.version), item)

    item_ids = get_item_ids(session, set(unique_items))
    latest_states = get_latest_states(session, marketplace.id)

    written = 0
    for key, item in unique_items.items():
        item_id = item_ids[key]
        state = (item.min_price_minor, item.quantity, item.currency)
        if latest_states.get(item_id) == state:
            continue
        session.add(
            MarketSnapshot(
                item_id=item_id,
                marketplace_id=marketplace.id,
                collected_at=collected_at,
                price_minor=item.min_price_minor,
                currency=item.currency,
                listings_count=item.quantity,
                volume=None,
            )
        )
        written += 1

    session.flush()
    return written


def get_known_item_keys(session: Session) -> set[ItemKey]:
    rows = session.execute(select(Item.market_hash_name, Item.version))
    return {(row.market_hash_name, row.version) for row in rows}