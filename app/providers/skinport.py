from decimal import ROUND_HALF_UP, Decimal
from urllib.parse import urlparse

import httpx
from pydantic import BaseModel

from app.market import MarketItem, normalize_name

BASE_URL = "https://api.skinport.com"
ITEMS_PATH = "/v1/items"
CS2_APP_ID = 730


class SkinportItem(BaseModel):
    market_hash_name: str
    version: str | None = None
    currency: str
    min_price: float | None = None
    quantity: int
    market_page: str | None = None


def to_minor_units(price: float | None) -> int | None:
    if price is None:
        return None
    cents = Decimal(str(price)) * 100
    return int(cents.quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def category_from_market_page(market_page: str | None) -> str:
    if not market_page:
        return "unknown"
    parts = urlparse(market_page).path.strip("/").split("/")
    return parts[1] if len(parts) > 1 else "unknown"


def to_market_item(raw: SkinportItem) -> MarketItem:
    return MarketItem(
        market_hash_name=normalize_name(raw.market_hash_name),
        version=raw.version,
        category=category_from_market_page(raw.market_page),
        currency=raw.currency,
        min_price_minor=to_minor_units(raw.min_price),
        quantity=raw.quantity,
    )


class SkinportProvider:
    def __init__(self, client: httpx.Client):
        self._client = client

    def fetch_items(self, currency: str = "EUR") -> list[MarketItem]:
        response = self._client.get(
            ITEMS_PATH,
            params={"app_id": CS2_APP_ID, "currency": currency},
            headers={"Accept-Encoding": "br"},
        )
        response.raise_for_status()
        return [to_market_item(SkinportItem.model_validate(raw)) for raw in response.json()]


def create_client() -> httpx.Client:
    return httpx.Client(base_url=BASE_URL, timeout=30)