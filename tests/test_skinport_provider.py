import httpx
import pytest
from pydantic import ValidationError

from app.market import MarketItem
from app.providers.skinport import (
    BASE_URL,
    SkinportProvider,
    category_from_market_page,
    to_minor_units,
)

# Образец взят из реального ответа Skinport /v1/items (21.11.2026), а не придуман.
REAL_ITEM = {
    "market_hash_name": "AK-47 | Baroque Purple (Well-Worn)",
    "version": None,
    "currency": "EUR",
    "suggested_price": 2.96,
    "item_page": "https://skinport.com/item/ak-47-baroque-purple-well-worn",
    "market_page": "https://skinport.com/market/rifle/ak-47?item=Baroque%20Purple",
    "min_price": 2.48,
    "max_price": 10,
    "mean_price": 6.02,
    "median_price": 5.82,
    "quantity": 12,
    "created_at": 1575431471,
    "updated_at": 1795278013,
}


def make_provider(handler):
    client = httpx.Client(base_url=BASE_URL, transport=httpx.MockTransport(handler))
    return SkinportProvider(client)


def respond_with(payload, status_code=200):
    requests = []

    def handler(request):
        requests.append(request)
        return httpx.Response(status_code, json=payload)

    return handler, requests


@pytest.mark.parametrize(
    ("price", "expected"),
    [
        (11.33, 1133),
        (0.29, 29),
        (10, 1000),
        (None, None),
    ],
)
def test_to_minor_units(price, expected):
    assert to_minor_units(price) == expected


@pytest.mark.parametrize(
    ("market_page", "expected"),
    [
        ("https://skinport.com/market/rifle/ak-47?item=Baroque%20Purple", "rifle"),
        ("https://skinport.com/market/agent/maximus", "agent"),
        (None, "unknown"),
    ],
)
def test_category_from_market_page(market_page, expected):
    assert category_from_market_page(market_page) == expected


def test_fetch_items_converts_real_response():
    handler, _ = respond_with([REAL_ITEM])
    items = make_provider(handler).fetch_items()

    assert items == [
        MarketItem(
            market_hash_name="AK-47 | Baroque Purple (Well-Worn)",
            version=None,
            category="rifle",
            currency="EUR",
            min_price_minor=248,
            quantity=12,
        )
    ]


def test_fetch_items_sends_expected_request():
    handler, requests = respond_with([])
    make_provider(handler).fetch_items()

    request = requests[0]
    assert request.url.path == "/v1/items"
    assert request.url.params["app_id"] == "730"
    assert request.url.params["currency"] == "EUR"
    assert "tradable" not in request.url.params
    assert request.headers["accept-encoding"] == "br"


def test_out_of_stock_item_has_no_price_and_zero_quantity():
    handler, _ = respond_with([{**REAL_ITEM, "min_price": None, "quantity": 0}])
    item = make_provider(handler).fetch_items()[0]

    assert item.min_price_minor is None
    assert item.quantity == 0


def test_item_name_whitespace_is_normalized():
    raw = {**REAL_ITEM, "market_hash_name": "Sticker | Ninjas in Pyjamas  | Cologne 2014"}
    handler, _ = respond_with([raw])
    item = make_provider(handler).fetch_items()[0]

    assert item.market_hash_name == "Sticker | Ninjas in Pyjamas | Cologne 2014"


def test_unexpected_response_format_raises_validation_error():
    broken = {key: value for key, value in REAL_ITEM.items() if key != "quantity"}
    handler, _ = respond_with([broken])

    with pytest.raises(ValidationError):
        make_provider(handler).fetch_items()


def test_server_error_raises_http_status_error():
    handler, _ = respond_with({"errors": []}, status_code=500)

    with pytest.raises(httpx.HTTPStatusError):
        make_provider(handler).fetch_items()