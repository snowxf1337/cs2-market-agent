import json
import re
from collections import defaultdict
from pathlib import Path

MAJORS = {
    "Katowice 2014", "Cologne 2014", "DreamHack 2014",
    "Katowice 2015", "Cologne 2015", "Cluj-Napoca 2015",
    "MLG Columbus 2016", "Cologne 2016",
    "Atlanta 2017", "Krakow 2017",
    "Boston 2018", "London 2018",
    "Katowice 2019", "Berlin 2019",
    "Stockholm 2021",
    "Antwerp 2022", "Rio 2022",
    "Paris 2023",
    "Copenhagen 2024", "Shanghai 2024",
    "Austin 2025", "Budapest 2025",
    "Cologne 2026",
}

items = json.loads(Path("data/skinport_items_full.json").read_text(encoding="utf-8"))

subjects = defaultdict(set)
for item in items:
    parts = item["market_hash_name"].split(" | ")
    if len(parts) != 3 or parts[0] != "Sticker" or parts[2] not in MAJORS:
        continue
    subject = re.sub(r"\s*\([^)]*\)$", "", parts[1])
    subjects[subject].add(parts[2])

lines = [
    f"{len(events):3}  {subject}"
    for subject, events in sorted(subjects.items(), key=lambda pair: -len(pair[1]))
]
output = Path("data/sticker_subjects.txt")
output.write_text("\n".join(lines), encoding="utf-8")
print("Unique subjects:", len(subjects))
print("Saved to", output)