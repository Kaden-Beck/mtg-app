from datetime import datetime, date
from sqlalchemy import String, Integer, Boolean, Text, DateTime, Date, ForeignKey, ARRAY, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db import Base
import uuid


class Card(Base):
    __tablename__ = "cards"

    id: Mapped[str] = mapped_column(String, primary_key=True)  # Scryfall UUID
    name: Mapped[str] = mapped_column(String, nullable=False, index=True)
    set_code: Mapped[str] = mapped_column(String, nullable=False)
    set_name: Mapped[str] = mapped_column(String, nullable=False)
    collector_number: Mapped[str] = mapped_column(String, nullable=False)
    mana_cost: Mapped[str | None] = mapped_column(String)
    cmc: Mapped[int] = mapped_column(Integer, default=0)
    type_line: Mapped[str] = mapped_column(String, nullable=False)
    oracle_text: Mapped[str | None] = mapped_column(Text)
    color_identity: Mapped[list] = mapped_column(ARRAY(String), default=[])
    rarity: Mapped[str] = mapped_column(String, nullable=False)
    price_usd: Mapped[int | None] = mapped_column(Integer)  # cents
    price_usd_foil: Mapped[int | None] = mapped_column(Integer)  # cents
    price_eur: Mapped[int | None] = mapped_column(Integer)  # cents
    image_uris: Mapped[dict | None] = mapped_column(JSONB)
    legalities: Mapped[dict | None] = mapped_column(JSONB)
    scryfall_data: Mapped[dict] = mapped_column(JSONB, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class CollectionItem(Base):
    __tablename__ = "collection"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    scryfall_id: Mapped[str] = mapped_column(
        String, ForeignKey("cards.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    foil: Mapped[bool] = mapped_column(Boolean, default=False)
    condition: Mapped[str] = mapped_column(String, default="NM")
    language: Mapped[str] = mapped_column(String, default="en")
    purchase_price_cents: Mapped[int | None] = mapped_column(Integer)
    acquired_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    notes: Mapped[str | None] = mapped_column(Text)
    card: Mapped["Card"] = relationship("Card")


class Deck(Base):
    __tablename__ = "decks"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    format: Mapped[str] = mapped_column(String, default="commander")
    description: Mapped[str | None] = mapped_column(Text)
    commander_id: Mapped[str | None] = mapped_column(String, ForeignKey("cards.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    deck_cards: Mapped[list["DeckCard"]] = relationship(
        "DeckCard", back_populates="deck", cascade="all, delete-orphan"
    )


class DeckCard(Base):
    __tablename__ = "deck_cards"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    deck_id: Mapped[str] = mapped_column(
        String, ForeignKey("decks.id", ondelete="CASCADE"), nullable=False, index=True
    )
    scryfall_id: Mapped[str] = mapped_column(
        String, ForeignKey("cards.id", ondelete="RESTRICT"), nullable=False
    )
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    board: Mapped[str] = mapped_column(String, default="mainboard")
    categories: Mapped[list] = mapped_column(ARRAY(String), default=[])
    foil: Mapped[bool] = mapped_column(Boolean, default=False)
    deck: Mapped["Deck"] = relationship("Deck", back_populates="deck_cards")
    card: Mapped["Card"] = relationship("Card")


class PriceHistory(Base):
    __tablename__ = "price_history"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    scryfall_id: Mapped[str] = mapped_column(
        String, ForeignKey("cards.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    price_usd: Mapped[int | None] = mapped_column(Integer)
    price_usd_foil: Mapped[int | None] = mapped_column(Integer)
    price_eur: Mapped[int | None] = mapped_column(Integer)
    snapshot_date: Mapped[date] = mapped_column(Date, nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class EdhrecCache(Base):
    __tablename__ = "edhrec_cache"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    slug: Mapped[str] = mapped_column(String, nullable=False, unique=True, index=True)
    data: Mapped[dict] = mapped_column(JSONB, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
