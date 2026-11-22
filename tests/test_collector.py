from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select

from app.collectors.collector import run_once
from app.database.models import CollectionRun, Item, MarketSnapshot
from app.market import FetchResult, MarketItem
from app.providers.errors import ProviderUnavailableError, RateLimitedError
from app.watchlist import Watchlist

START = datetime(2026, 11, 22, 12, 0, tzinfo=UTC)
WATCHLIST = Watchlist(teams=frozenset({"natus vincere"}), item_names=frozenset())


def make_item(name, category="sticker", price=350, quantity=120):
    return MarketItem(
        market_hash_name=name,
        version=None,
        category=category,
        currency="EUR",
        min_price_minor=price,
        quantity=quantity,
    )


TEAM_STICKER = make_item("Sticker | Natus Vincere (Holo) | Paris 2023")
UNTRACKED_SKIN = make_item("AK-47 | Redline (Field-Tested)", category="rifle", price=1250, quantity=400)


class FakeProvider:
    code = "skinport"
    name = "Skinport"

    def __init__(self, result=None, error=None):
        self.result = result
        self.error = error

    def fetch_items(self):
        if self.error is not None:
            raise self.error
        return self.result


def fixed_clock():
    return START


def count(session, model):
    return session.scalar(select(func.count()).select_from(model))


def test_successful_run_saves_only_tracked_items(session):
    provider = FakeProvider(FetchResult(items=[TEAM_STICKER, UNTRACKED_SKIN], skipped=1))
    run = run_once(session, provider, WATCHLIST, now=fixed_clock)

    assert run.status == "success"
    assert run.items_seen == 3
    assert run.items_tracked == 1
    assert run.items_skipped == 1
    assert run.snapshots_written == 1
    assert count(session, Item) == 1
    assert count(session, MarketSnapshot) == 1


def test_second_identical_run_writes_no_snapshots(session):
    provider = FakeProvider(FetchResult(items=[TEAM_STICKER]))
    run_once(session, provider, WATCHLIST, now=fixed_clock)
    second = run_once(session, provider, WATCHLIST, now=lambda: START + timedelta(minutes=5))

    assert second.snapshots_written == 0
    assert count(session, CollectionRun) == 2


def test_tracked_item_stays_tracked_after_leaving_rules(session):
    skin = make_item("FAMAS | Survivor Z (Factory New)", category="rifle", price=2500, quantity=5)
    pumped = make_item("FAMAS | Survivor Z (Factory New)", category="rifle", price=50_000, quantity=2)

    run_once(session, FakeProvider(FetchResult(items=[skin])), WATCHLIST, now=fixed_clock)
    second = run_once(
        session,
        FakeProvider(FetchResult(items=[pumped])),
        WATCHLIST,
        now=lambda: START + timedelta(minutes=5),
    )

    assert second.items_tracked == 1
    assert second.snapshots_written == 1


def test_rate_limit_is_recorded_in_journal(session):
    provider = FakeProvider(error=RateLimitedError("Skinport rate limit exceeded"))
    run = run_once(session, provider, WATCHLIST, now=fixed_clock)

    assert run.status == "rate_limited"
    assert run.error == "Skinport rate limit exceeded"
    assert run.items_seen is None
    assert count(session, MarketSnapshot) == 0


def test_provider_failure_is_recorded_in_journal(session):
    provider = FakeProvider(error=ProviderUnavailableError("Skinport request timed out"))
    run = run_once(session, provider, WATCHLIST, now=fixed_clock)

    assert run.status == "failed"
    assert run.error == "Skinport request timed out"


def test_run_times_are_recorded(session):
    times = iter([START, START + timedelta(seconds=30)])
    provider = FakeProvider(FetchResult(items=[TEAM_STICKER]))
    run = run_once(session, provider, WATCHLIST, now=lambda: next(times))
    session.expire_all()

    snapshot = session.scalars(select(MarketSnapshot)).one()
    assert run.started_at == START
    assert run.finished_at == START + timedelta(seconds=30)
    assert snapshot.collected_at == START