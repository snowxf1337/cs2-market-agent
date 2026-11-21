import json
from pathlib import Path

import httpx

URL = "https://api.skinport.com/v1/items"
PARAMS = {"app_id": 730, "currency": "EUR"}
HEADERS = {"Accept-Encoding": "br"}

response = httpx.get(URL, params=PARAMS, headers=HEADERS, timeout=30)

print("Status:", response.status_code)
print("Content-Encoding:", response.headers.get("content-encoding"))
response.raise_for_status()

items = response.json()
print("Items total:", len(items))

output = Path("data/skinport_items_full.json")
output.parent.mkdir(exist_ok=True)
output.write_text(json.dumps(items, indent=2, ensure_ascii=False), encoding="utf-8")
print("Saved full response to", output)