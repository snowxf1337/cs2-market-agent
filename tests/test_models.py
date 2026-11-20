from app.database.models import MarketSnapshot


def test_optional_market_fields_are_nullable():
    columns = MarketSnapshot.__table__.columns
    assert columns["price_minor"].nullable
    assert columns["listings_count"].nullable
    assert columns["volume"].nullable


def test_required_snapshot_fields_are_not_nullable():
    columns = MarketSnapshot.__table__.columns
    for name in ("item_id", "marketplace_id", "collected_at", "currency"):
        assert not columns[name].nullable, f"{name} must be required"