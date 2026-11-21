from dataclasses import dataclass


@dataclass(frozen=True)
class MarketItem:
    market_hash_name: str
    version: str | None
    category: str
    currency: str
    min_price_minor: int | None
    quantity: int