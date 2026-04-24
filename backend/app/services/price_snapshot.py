import uuid
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from app.models.models import CollectionItem, Card, PriceHistory


async def take_price_snapshot(db: AsyncSession) -> int:
    today = date.today().isoformat()

    result = await db.execute(select(CollectionItem.scryfall_id).distinct())
    ids = [row[0] for row in result]

    count = 0
    for scryfall_id in ids:
        card_result = await db.execute(
            select(Card.price_usd, Card.price_usd_foil, Card.price_eur).where(
                Card.id == scryfall_id
            )
        )
        card = card_result.first()
        if not card:
            continue

        stmt = (
            pg_insert(PriceHistory)
            .values(
                id=str(uuid.uuid4()),
                scryfall_id=scryfall_id,
                price_usd=card.price_usd,
                price_usd_foil=card.price_usd_foil,
                price_eur=card.price_eur,
                snapshot_date=today,
            )
            .on_conflict_do_nothing()
        )

        await db.execute(stmt)
        count += 1

    await db.commit()
    return count
