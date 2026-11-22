from datetime import datetime

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    MetaData,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_N_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)


class Marketplace(Base):
    __tablename__ = "marketplaces"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(50), unique=True)
    name: Mapped[str] = mapped_column(String(100))


class Item(Base):
    __tablename__ = "items"
    __table_args__ = (
        UniqueConstraint(
            "market_hash_name",
            "version",
            postgresql_nulls_not_distinct=True,
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    market_hash_name: Mapped[str] = mapped_column(String(255))
    version: Mapped[str | None] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class MarketSnapshot(Base):
    __tablename__ = "market_snapshots"
    __table_args__ = (
        UniqueConstraint("item_id", "marketplace_id", "collected_at"),
        CheckConstraint("price_minor >= 0", name="price_minor_non_negative"),
        CheckConstraint("listings_count >= 0", name="listings_count_non_negative"),
        CheckConstraint("volume >= 0", name="volume_non_negative"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("items.id"))
    marketplace_id: Mapped[int] = mapped_column(ForeignKey("marketplaces.id"))
    collected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    price_minor: Mapped[int | None] = mapped_column(BigInteger)
    currency: Mapped[str] = mapped_column(String(3))
    listings_count: Mapped[int | None]
    volume: Mapped[int | None]


class CollectionRun(Base):
    __tablename__ = "collection_runs"
    __table_args__ = (
        CheckConstraint(
            "status IN ('success', 'failed', 'rate_limited')",
            name="status_valid",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    marketplace_id: Mapped[int] = mapped_column(ForeignKey("marketplaces.id"))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(20))
    items_seen: Mapped[int | None]
    items_tracked: Mapped[int | None]
    items_skipped: Mapped[int | None]
    snapshots_written: Mapped[int | None]
    error: Mapped[str | None] = mapped_column(Text)