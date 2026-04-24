import strawberry
import uuid
from strawberry.types import Info
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.models.models import Deck, DeckCard
from app.graphql.types import DeckType, DeckCardType


@strawberry.type
class DecksQuery:
    @strawberry.field
    async def decks(self, info: Info) -> list[DeckType]:
        db = info.context["db"]
        result = await db.execute(select(Deck).options(selectinload(Deck.deck_cards)))
        return [_to_deck_type(d) for d in result.scalars()]

    @strawberry.field
    async def deck(self, info: Info, id: str) -> DeckType | None:
        db = info.context["db"]
        result = await db.execute(
            select(Deck)
            .where(Deck.id == id)
            .options(selectinload(Deck.deck_cards).selectinload(DeckCard.card))
        )
        deck = result.scalar_one_or_none()
        return _to_deck_type(deck) if deck else None


@strawberry.type
class DecksMutation:
    @strawberry.mutation
    async def create_deck(
        self,
        info: Info,
        name: str,
        format: str = "commander",
        commander_id: str | None = None,
    ) -> DeckType:
        db = info.context["db"]
        deck = Deck(
            id=str(uuid.uuid4()), name=name, format=format, commander_id=commander_id
        )
        db.add(deck)
        await db.commit()
        result = await db.execute(
            select(Deck)
            .where(Deck.id == deck.id)
            .options(selectinload(Deck.deck_cards))
        )
        return _to_deck_type(result.scalar_one())

    @strawberry.mutation
    async def add_card_to_deck(
        self,
        info: Info,
        deck_id: str,
        scryfall_id: str,
        quantity: int = 1,
        board: str = "mainboard",
        categories: list[str] = [],
    ) -> DeckCardType:
        db = info.context["db"]
        dc = DeckCard(
            id=str(uuid.uuid4()),
            deck_id=deck_id,
            scryfall_id=scryfall_id,
            quantity=quantity,
            board=board,
            categories=categories,
        )
        db.add(dc)
        await db.commit()
        await db.refresh(dc)
        return _to_deck_card_type(dc)


def _to_deck_card_type(dc: DeckCard) -> DeckCardType:
    return DeckCardType(
        id=dc.id,
        deck_id=dc.deck_id,
        scryfall_id=dc.scryfall_id,
        quantity=dc.quantity,
        board=dc.board,
        categories=dc.categories or [],
        foil=dc.foil,
    )


def _to_deck_type(d: Deck) -> DeckType:
    return DeckType(
        id=d.id,
        name=d.name,
        format=d.format,
        description=d.description,
        commander_id=d.commander_id,
        created_at=d.created_at,
        updated_at=d.updated_at,
        deck_cards=[_to_deck_card_type(dc) for dc in (d.deck_cards or [])],
    )


def is_legal_in_commander(
    commander_identity: list[str], card_identity: list[str]
) -> bool:
    return all(c in commander_identity for c in card_identity)
