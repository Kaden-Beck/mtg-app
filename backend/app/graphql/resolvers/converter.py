import enum
import strawberry
from strawberry.types import Info
from app.services.converter import convert
from app.graphql.types import ConversionResultType


@strawberry.enum
class CollectionFormat(enum.Enum):
    manabox = "manabox"
    moxfield = "moxfield"
    archidekt = "archidekt"


@strawberry.type
class ConverterMutation:
    @strawberry.mutation
    async def convert_csv(
        self,
        info: Info,
        csv: str,
        from_format: CollectionFormat,
        to_format: CollectionFormat,
    ) -> ConversionResultType:
        db = info.context["db"]
        output, count = await convert(csv, from_format.value, to_format.value, db)
        return ConversionResultType(csv=output, count=count)
