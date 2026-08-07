import strawberry
from strawberry.types import Info


@strawberry.type
class PricesQuery:
    @strawberry.field
    async def price_history_placeholder(self, info: Info) -> str:
        """Stub. Replaced in Lesson 14 (Price Snapshot Service + Resolver)."""
        return "price_history not yet implemented"
