import strawberry
import uuid
from strawberry.types import Info
from sqlalchemy import select
from app.models.models import CollectionItem
from app.graphql.types import CollectionItemType


def _to_type(item: CollectionItem) -> CollectionItemType:
    """Map SQLAlchemy to Strawberry

    Args:
        item (CollectionItem): SQL Alchemy Type

    Returns:
        CollectionItemType: Strawberry GraphQL Type
    """
    return CollectionItemType(
        id=item.id,
        scryfall_id=item.scryfall_id,
        quantity=item.quantity,
        foil=item.foil,
        condition=item.condition,
        language=item.language,
        purchase_price_cents=item.purchase_price_cents,
        acquired_at=item.acquired_at,
    )


@strawberry.type
class CollectionQuery:
    @strawberry.field
    async def collection(self, info: Info) -> list[CollectionItemType]:
        db = info.context["db"]
        result = await db.execute(select(CollectionItem))
        return [_to_type(item) for item in result.scalars()]


@strawberry.type
class CollectionMutation:
    @strawberry.mutation
    async def add_to_collection(
        self,
        info: Info,
        scryfall_id: str,
        quantity: int = 1,
        foil: bool = False,
        condition: str = "NM",
        language: str = "en",
        purchase_price_cents: int | None = None,
    ) -> CollectionItemType:
        db = info.context["db"]
        item = CollectionItem(
            id=str(uuid.uuid4()),
            scryfall_id=scryfall_id,
            quantity=quantity,
            foil=foil,
            condition=condition,
            language=language,
            purchase_price_cents=purchase_price_cents,
        )
        db.add(item)
        await db.commit()
        await db.refresh(item)
        return _to_type(item)
