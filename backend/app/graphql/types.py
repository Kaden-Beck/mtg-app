import strawberry
from typing import Optional
from datetime import datetime


@strawberry.type
class CardType:
    id: str
    name: str
    set_code: str
    set_name: str
    collector_number: str
    mana_cost: Optional[str]
    cmc: int
    type_line: str
    oracle_text: Optional[str]
    color_identity: list[str]
    rarity: str
    price_usd: Optional[int]  # cents
    price_usd_foil: Optional[int]  # cents
    price_eur: Optional[int]  # cents


@strawberry.type
class CollectionItemType:
    id: str
    scryfall_id: str
    quantity: int
    foil: bool
    condition: str
    language: str
    purchase_price_cents: Optional[int]
    acquired_at: datetime
    card: Optional[CardType] = None


@strawberry.type
class DeckCardType:
    id: str
    deck_id: str
    scryfall_id: str
    quantity: int
    board: str
    categories: list[str]
    foil: bool
    card: Optional[CardType] = None


@strawberry.type
class DeckType:
    id: str
    name: str
    format: str
    description: Optional[str]
    commander_id: Optional[str]
    created_at: datetime
    updated_at: datetime
    deck_cards: list[DeckCardType] = strawberry.field(default_factory=list)


@strawberry.type
class PriceHistoryType:
    id: str
    scryfall_id: str
    price_usd: Optional[int]
    price_usd_foil: Optional[int]
    price_eur: Optional[int]
    snapshot_date: str
    recorded_at: datetime


@strawberry.type
class ConversionResultType:
    csv: str
    count: int
