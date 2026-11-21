import json
import re
import tomllib
from collections import Counter
from pathlib import Path

MAJORS = {
    "Katowice 2014", "Cologne 2014", "DreamHack 2014",
    "Katowice 2015", "Cologne 2015", "Cluj-Napoca 2015",
    "MLG Columbus 2016", "Cologne 2016", "Atlanta 2017", "Krakow 2017",
    "Boston 2018", "London 2018", "Katowice 2019", "Berlin 2019",
    "Stockholm 2021", "Antwerp 2022", "Rio 2022", "Paris 2023",
    "Copenhagen 2024", "Shanghai 2024", "Austin 2025", "Budapest 2025",
    "Cologne 2026",
}


def normalize(text):
    return " ".join(text.split())


def sticker_subject(name):
    parts = [normalize(part) for part in name.split("|")]
    if len(parts) != 3 or parts[0] != "Sticker" or parts[2] not in MAJORS:
        return None
    return re.sub(r"\s*\([^)]*\)$", "", parts[1]).strip()


def buyout_cost(item):
    return item["mean_price"] * item["quantity"]


config = tomllib.loads(Path("config/watchlist.toml").read_text(encoding="utf-8"))
teams = {team.casefold(): team for team in config["stickers"]["teams"]}
items = json.loads(Path("data/skinport_items_full.json").read_text(encoding="utf-8"))

matched = []
per_team = Counter()
for item in items:
    subject = sticker_subject(item["market_hash_name"])
    if subject is not None and subject.casefold() in teams:
        matched.append(item)
        per_team[teams[subject.casefold()]] += 1

missing = [team for team in config["stickers"]["teams"] if per_team[team] == 0]
print("Teams in config:", len(config["stickers"]["teams"]))
print("Teams NOT found (check spelling):", missing or "none")

in_stock = [item for item in matched if item["quantity"] > 0]
print("\nTeam stickers found:", len(matched))
print("Of them in stock now:", len(in_stock))

print("\nIn-stock stickers by buyout cost (mean_price x quantity):")
for limit in (100, 500, 2000, 5000, 20000):
    count = sum(1 for item in in_stock if buyout_cost(item) <= limit)
    print(f"  <= {limit:>6} EUR: {count}")