from typing import Protocol

from app.market import FetchResult


class MarketProvider(Protocol):
    code: str
    name: str

    def fetch_items(self) -> FetchResult: ...