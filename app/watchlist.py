import re
import tomllib
from dataclasses import dataclass
from pathlib import Path

from app.market import MarketItem, normalize_name

MAJORS = frozenset({
    "Katowice 2014", "Cologne 2014", "DreamHack 2014",
    "Katowice 2015", "Cologne 2015", "Cluj-Napoca 2015",
    "MLG Columbus 2016", "Cologne 2016", "Atlanta 2017", "Krakow 2017",
    "Boston 2018", "London 2018", "Katowice 2019", "Berlin 2019",
    "Stockholm 2021", "Antwerp 2022", "Rio 2022", "Paris 2023",
    "Copenhagen 2024", "Shanghai 2024", "Austin 2025", "Budapest 2025",
    "Cologne 2026",
})

TRACKED_CATEGORIES = frozenset({"agent"})
SKIN_WEARS = ("(Factory New)", "(Minimal Wear)")
SKIN_MIN_PRICE_MINOR = 500
SKIN_MAX_PRICE_MINOR = 30_000
SKIN_MAX_QUANTITY = 10



def sticker_team(name: str) -> str | None:
    parts = [normalize_name(part) for part in name.split("|")]
    if len(parts) != 3 or parts[0] != "Sticker" or parts[2] not in MAJORS:
        return None
    return re.sub(r"\s*\([^)]*\)$", "", parts[1]).strip()


def is_candidate_skin(item: MarketItem) -> bool:
    name = normalize_name(item.market_hash_name)
    return (
        name.endswith(SKIN_WEARS)
        and not name.startswith("★")
        and item.min_price_minor is not None
        and SKIN_MIN_PRICE_MINOR <= item.min_price_minor <= SKIN_MAX_PRICE_MINOR
        and item.quantity <= SKIN_MAX_QUANTITY
    )


@dataclass(frozen=True)
class Watchlist:
    teams: frozenset[str]
    item_names: frozenset[str]

    def is_tracked(self, item: MarketItem) -> bool:
        name = normalize_name(item.market_hash_name)
        if name in self.item_names:
            return True
        if item.category in TRACKED_CATEGORIES:
            return True
        if name.endswith(" Case"):
            return True
        team = sticker_team(name)
        if team is not None and team.casefold() in self.teams:
            return True
        return is_candidate_skin(item)


def load_watchlist(path: Path) -> Watchlist:
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    return Watchlist(
        teams=frozenset(team.casefold() for team in data["stickers"]["teams"]),
        item_names=frozenset(normalize_name(name) for name in data["items"]["names"]),
    )