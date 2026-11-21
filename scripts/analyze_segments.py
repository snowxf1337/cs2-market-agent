import json
import re
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse

items = json.loads(Path("data/skinport_items_full.json").read_text(encoding="utf-8"))
print("Items total:", len(items))


def category(item):
    if not item["market_page"]:
        return "?"
    parts = urlparse(item["market_page"]).path.strip("/").split("/")
    return parts[1] if len(parts) > 1 else "?"


print("\nCategories from market_page:")
for name, count in Counter(category(item) for item in items).most_common():
    print(f"{count:7}  {name}")

stickers = [item for item in items if item["market_hash_name"].startswith("Sticker | ")]
events = Counter(
    item["market_hash_name"].split(" | ")[-1]
    for item in stickers
    if re.search(r"\b\d{4}$", item["market_hash_name"])
)
print("\nStickers total:", len(stickers))
print("Stickers whose name ends with a year:", sum(events.values()))
for event, count in events.most_common(30):
    print(f"{count:7}  {event}")

cases = [item for item in items if item["market_hash_name"].endswith(" Case")]
print("\nCases:", len(cases))

wears = ("(Factory New)", "(Minimal Wear)")
skins = [
    item
    for item in items
    if item["market_hash_name"].endswith(wears)
    and not item["market_hash_name"].startswith("★")
    and item["min_price"] is not None
    and 5 <= item["min_price"] <= 300
]
print("\nFN/MW weapon skins priced 5-300 EUR:", len(skins))
for limit in (5, 10, 20, 50):
    count = sum(1 for item in skins if item["quantity"] <= limit)
    print(f"  with quantity <= {limit}: {count}")