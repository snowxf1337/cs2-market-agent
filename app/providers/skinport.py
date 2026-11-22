from decimal import ROUND_HALF_UP, Decimal
from urllib.parse import urlparse

import httpx
from pydantic import BaseModel, ValidationError

from app.market import FetchResult, MarketItem, normalize_name
from app.providers.errors import (
    ProviderResponseError,
    ProviderUnavailableError,
    RateLimitedError,
)

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
    code = "skinport"
    name = "Skinport"
    
    def __init__(self, client: httpx.Client):
        self._client = client

    def fetch_items(self, currency: str = "EUR") -> FetchResult:
        try:
            response = self._client.get(
                ITEMS_PATH,
                params={"app_id": CS2_APP_ID, "currency": currency},
                headers={"Accept-Encoding": "br"},
            )
        except httpx.TimeoutException as error:
            raise ProviderUnavailableError("Skinport request timed out") from error
        except httpx.TransportError as error:
            raise ProviderUnavailableError(f"Skinport is unreachable: {error}") from error

        if response.status_code == 429:
            raise RateLimitedError("Skinport rate limit exceeded")
        if response.status_code >= 500:
            raise ProviderUnavailableError(f"Skinport server error {response.status_code}")
        if response.status_code != 200:
            raise ProviderResponseError(
                f"Unexpected status {response.status_code}: {response.text[:200]}"
            )

        try:
            payload = response.json()
        except ValueError as error:
            raise ProviderResponseError("Skinport returned invalid JSON") from error
        if not isinstance(payload, list):
            raise ProviderResponseError("Expected a list of items from Skinport")

        items = []
        skipped = 0
        for raw in payload:
            try:
                items.append(to_market_item(SkinportItem.model_validate(raw)))
            except ValidationError:
                skipped += 1

        if payload and not items:
            raise ProviderResponseError("All items failed validation, the format may have changed")
        return FetchResult(items=items, skipped=skipped)


def create_client() -> httpx.Client:
    return httpx.Client(base_url=BASE_URL, timeout=30)