from dataclasses import dataclass


def normalize_name(name: str) -> str:
    return " ".join(name.split())


@dataclass(frozen=True)
class MarketItem:
    market_hash_name: str
    version: str | None
    category: str
    currency: str
    min_price_minor: int | None
    quantity: int