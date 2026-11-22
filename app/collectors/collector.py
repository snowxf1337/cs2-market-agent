from collections.abc import Callable
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.database.models import CollectionRun, Marketplace
from app.database.repository import (
    get_known_item_keys,
    get_or_create_marketplace,
    save_snapshots,
)
from app.providers.base import MarketProvider
from app.providers.errors import ProviderError, RateLimitedError
from app.watchlist import Watchlist


def utc_now() -> datetime:
    return datetime.now(UTC)


def run_once(
    session: Session,
    provider: MarketProvider,
    watchlist: Watchlist,
    now: Callable[[], datetime] = utc_now,
) -> CollectionRun:
    started_at = now()
    marketplace = get_or_create_marketplace(session, provider.code, provider.name)
    session.commit()

    try:
        result = provider.fetch_items()
    except RateLimitedError as error:
        return record_run(session, marketplace, started_at, now(), "rate_limited", error=str(error))
    except ProviderError as error:
        return record_run(session, marketplace, started_at, now(), "failed", error=str(error))

    known_keys = get_known_item_keys(session)
    tracked = [
        item
        for item in result.items
        if watchlist.is_tracked(item) or (item.market_hash_name, item.version) in known_keys
    ]
    written = save_snapshots(session, marketplace, tracked, started_at)

    return record_run(
        session,
        marketplace,
        started_at,
        now(),
        "success",
        items_seen=len(result.items) + result.skipped,
        items_tracked=len(tracked),
        items_skipped=result.skipped,
        snapshots_written=written,
    )


def record_run(
    session: Session,
    marketplace: Marketplace,
    started_at: datetime,
    finished_at: datetime,
    status: str,
    **details,
) -> CollectionRun:
    run = CollectionRun(
        marketplace_id=marketplace.id,
        started_at=started_at,
        finished_at=finished_at,
        status=status,
        **details,
    )
    session.add(run)
    session.commit()
    return run