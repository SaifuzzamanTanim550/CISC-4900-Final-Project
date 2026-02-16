from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import relationship

from src.models.base import Base


class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True)
    name = Column(String(120), nullable=False, unique=True)
    category = Column(String(50), nullable=False)
    has_variants = Column(Boolean, nullable=False, default=False)
    is_active = Column(Boolean, nullable=False, default=True)

    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    variants = relationship("ItemVariant", back_populates="item")
    transactions = relationship("Transaction", back_populates="item")


class ItemVariant(Base):
    __tablename__ = "item_variants"

    id = Column(Integer, primary_key=True)
    item_id = Column(Integer, ForeignKey("items.id"), nullable=False)

    variant_name = Column(String(20), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)

    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    item = relationship("Item", back_populates="variants")
    transactions = relationship("Transaction", back_populates="item_variant")

    __table_args__ = (
        UniqueConstraint("item_id", "variant_name", name="uq_item_variants_item_id_variant_name"),
    )


class Location(Base):
    __tablename__ = "locations"

    id = Column(Integer, primary_key=True)
    name = Column(String(120), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)

    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    events = relationship("Event", back_populates="location")
    transactions = relationship("Transaction", back_populates="location")


class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True)
    name = Column(String(160), nullable=False)
    event_type = Column(String(80), nullable=False)
    event_date = Column(Date, nullable=False)

    location_id = Column(Integer, ForeignKey("locations.id"), nullable=True)
    notes = Column(Text, nullable=True)

    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    location = relationship("Location", back_populates="events")
    transactions = relationship("Transaction", back_populates="event")


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True)

    transaction_type = Column(String(3), nullable=False)

    item_id = Column(Integer, ForeignKey("items.id"), nullable=False)
    item_variant_id = Column(Integer, ForeignKey("item_variants.id"), nullable=True)

    location_id = Column(Integer, ForeignKey("locations.id"), nullable=False)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=True)

    quantity = Column(Integer, nullable=False)

    reason = Column(Text, nullable=False)
    created_by = Column(String(120), nullable=False)

    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    item = relationship("Item", back_populates="transactions")
    item_variant = relationship("ItemVariant", back_populates="transactions")
    location = relationship("Location", back_populates="transactions")
    event = relationship("Event", back_populates="transactions")

    __table_args__ = (
        CheckConstraint(
            "transaction_type IN ('IN','OUT')",
            name="ck_transactions_transaction_type",
        ),
        CheckConstraint(
            "quantity > 0",
            name="ck_transactions_quantity_positive",
        ),
    )


class Setting(Base):
    __tablename__ = "settings"

    id = Column(Integer, primary_key=True)
    key = Column(String(120), nullable=False, unique=True)
    value = Column(Text, nullable=False)

    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class LowStockAlert(Base):
    __tablename__ = "low_stock_alerts"

    id = Column(Integer, primary_key=True)

    location_id = Column(Integer, ForeignKey("locations.id"), nullable=False)
    item_id = Column(Integer, ForeignKey("items.id"), nullable=False)
    item_variant_id = Column(Integer, ForeignKey("item_variants.id"), nullable=True)

    threshold = Column(Integer, nullable=False)

    triggered_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    location = relationship("Location")
    item = relationship("Item")
    item_variant = relationship("ItemVariant")

    __table_args__ = (
        CheckConstraint(
            "threshold > 0",
            name="ck_low_stock_alerts_threshold_positive",
        ),
    )
