import strawberry
from strawberry.types import Info
from sqlalchemy import select, or_, func
from app.models.models import Card
from app.graphql.types import CardType
from typing import Optional


def _to_card_type(c: Card) -> CardType:
    """Takes a Card passed from Postgres and maps it to the CardType GraphQL Schema

    Args:
        c (Card): MTG Card Data as received from PostgreSQL via SQLAlchemy

    Returns:
        CardType: GraphQL Schema for a MTG Card
    """
    return CardType(
        id=c.id,
        name=c.name,
        set_code=c.set_code,
        set_name=c.set_name,
        collector_number=c.collector_number,
        mana_cost=c.mana_cost,
        cmc=c.cmc,
        type_line=c.type_line,
        oracle_text=c.oracle_text,
        color_identity=c.color_identity or [],
        rarity=c.rarity,
        price_usd=c.price_usd,
        price_usd_foil=c.price_usd_foil,
        price_eur=c.price_eur,
    )


@strawberry.type
class CardsQuery:
    """Strawberry GraphQL Card Query"""

    @strawberry.field
    async def search_cards(
        self, info: Info, query: str, limit: int = 20
    ) -> list[CardType]:
        db = info.context["db"]
        stmt = (
            select(Card)
            .where(func.lower(Card.name).contains(query.lower()))
            .limit(min(limit, 50))
        )
        result = await db.execute(stmt)

        return [_to_card_type(c) for c in result.scalars()]

    @strawberry.field
    async def card_by_id(self, info: Info, id: str) -> Optional[CardType]:
        db = info.context["db"]
        result = await db.execute(select(Card).where(Card.id == id))
        card = result.scalar_one_or_none()
        
        return _to_card_type(card) if card else None
