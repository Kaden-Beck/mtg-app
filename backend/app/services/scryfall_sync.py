import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert as pg_insert
from app.models.models import Card
# import asyncio

BULK_META_URL = "https://api.scryfall.com/bulk-data/default-cards"


def _price_cents(val: str | None) -> int | None:
    if val is None:
        return None
    try:
        return round(float(val) * 100)
    except (ValueError, TypeError):
        return None


async def sync_scryfall_bulk(db: AsyncSession) -> int:
    async with httpx.AsyncClient(timeout=300) as client:
        meta = (await client.get(BULK_META_URL)).json()
        download_url: str = meta["download_uri"]

        print(f"Downloading bulk data from {download_url}...")
        response = await client.get(download_url)
        card_array: list[dict] = response.json()

    print(f"Upserting {len(card_array)} cards...")
    BATCH = 500
    for i in range(0, len(card_array), BATCH):
        batch = card_array[i : i + BATCH]
        values = [
            {
                "id": c["id"],
                "name": c["name"],
                "set_code": c["set"],
                "set_name": c["set_name"],
                "collector_number": c["collector_number"],
                "mana_cost": c.get("mana_cost"),
                "cmc": round(c.get("cmc") or 0),
                "type_line": c.get("type_line", ""),
                "oracle_text": c.get("oracle_text"),
                "color_identity": c.get("color_identity", []),
                "rarity": c["rarity"],
                "price_usd": _price_cents(c.get("prices", {}).get("usd")),
                "price_usd_foil": _price_cents(c.get("prices", {}).get("usd_foil")),
                "price_eur": _price_cents(c.get("prices", {}).get("eur")),
                "image_uris": c.get("image_uris"),
                "legalities": c.get("legalities"),
                "scryfall_data": c,
            }
            for c in batch
        ]
        stmt = pg_insert(Card).values(values)
        stmt = stmt.on_conflict_do_update(
            index_elements=["id"],
            set_={
                "name": stmt.excluded.name,
                "price_usd": stmt.excluded.price_usd,
                "price_usd_foil": stmt.excluded.price_usd_foil,
                "price_eur": stmt.excluded.price_eur,
                "scryfall_data": stmt.excluded.scryfall_data,
            },
        )
        await db.execute(stmt)
        await db.commit()
        if i % 5000 == 0:
            print(f"  {i} / {len(card_array)}")

    print("Bulk sync complete.")
    return len(card_array)
