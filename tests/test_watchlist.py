from pathlib import Path

import pytest

from app.market import MarketItem
from app.watchlist import Watchlist, load_watchlist, normalize_name, sticker_team

WATCHLIST = Watchlist(
    teams=frozenset({"natus vincere", "virtus.pro"}),
    item_names=frozenset({"MP9 | Hydra (Factory New)"}),
)


def make_item(name, category="other", price=1000, quantity=50, version=None):
    return MarketItem(
        market_hash_name=name,
        version=version,
        category=category,
        currency="EUR",
        min_price_minor=price,
        quantity=quantity,
    )


def test_normalize_name_collapses_extra_spaces():
    assert normalize_name("Ninjas in  Pyjamas ") == "Ninjas in Pyjamas"


def test_sticker_team_strips_variant():
    assert sticker_team("Sticker | Natus Vincere (Holo) | Paris 2023") == "Natus Vincere"


def test_sticker_team_handles_double_spaces():
    assert sticker_team("Sticker | Ninjas in Pyjamas  | Cologne 2014") == "Ninjas in Pyjamas"


def test_sticker_team_ignores_non_major_events():
    assert sticker_team("Sticker | 100 Thieves (Holo) | 2020 RMR") is None


def test_sticker_team_ignores_sticker_slabs():
    assert sticker_team("Sticker Slab | 100 Thieves | Boston 2018") is None


def test_team_sticker_is_tracked_case_insensitively():
    item = make_item("Sticker | Virtus.Pro (Holo) | Katowice 2014", category="sticker")
    assert WATCHLIST.is_tracked(item)


def test_player_autograph_is_not_tracked():
    item = make_item("Sticker | s1mple | Paris 2023", category="sticker")
    assert not WATCHLIST.is_tracked(item)


def test_agent_is_tracked():
    assert WATCHLIST.is_tracked(make_item("Maximus | Sabre", category="agent"))


def test_case_is_tracked():
    assert WATCHLIST.is_tracked(make_item("Recoil Case", category="container"))


def test_item_from_manual_list_is_tracked():
    assert WATCHLIST.is_tracked(make_item("MP9 | Hydra (Factory New)", quantity=500))


def test_candidate_skin_is_tracked():
    item = make_item("FAMAS | Survivor Z (Factory New)", price=2500, quantity=5)
    assert WATCHLIST.is_tracked(item)


@pytest.mark.parametrize(
    ("price", "quantity"),
    [
        (500, 10),
        (30_000, 10),
    ],
)
def test_skin_profile_boundaries_are_included(price, quantity):
    item = make_item("FAMAS | Survivor Z (Factory New)", price=price, quantity=quantity)
    assert WATCHLIST.is_tracked(item)


@pytest.mark.parametrize(
    ("name", "price", "quantity"),
    [
        ("★ Karambit | Fade (Factory New)", 2500, 5),
        ("FAMAS | Survivor Z (Field-Tested)", 2500, 5),
        ("FAMAS | Survivor Z (Factory New)", 2500, 11),
        ("FAMAS | Survivor Z (Factory New)", 499, 5),
        ("FAMAS | Survivor Z (Factory New)", 30_001, 5),
        ("FAMAS | Survivor Z (Factory New)", None, 0),
    ],
)
def test_skin_outside_profile_is_not_tracked(name, price, quantity):
    assert not WATCHLIST.is_tracked(make_item(name, price=price, quantity=quantity))


def test_load_watchlist_reads_toml(tmp_path):
    config = tmp_path / "watchlist.toml"
    config.write_text(
        '[stickers]\nteams = ["Natus Vincere"]\n\n[items]\nnames = ["MP9  | Hydra (Factory New)"]\n',
        encoding="utf-8",
    )
    watchlist = load_watchlist(config)
    assert watchlist.teams == frozenset({"natus vincere"})
    assert watchlist.item_names == frozenset({"MP9 | Hydra (Factory New)"})


def test_project_watchlist_config_is_valid():
    watchlist = load_watchlist(Path("config/watchlist.toml"))
    assert len(watchlist.teams) > 100