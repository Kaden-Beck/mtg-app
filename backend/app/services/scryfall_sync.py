import math
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

import httpx
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import Card

# import asyncio

BULK_META_URL = "https://api.scryfall.com/bulk-data/default-cards"

_INVALID_PRICE_SENTINELS = {"", "—", "n/a", "na", "null"}


def _price_cents(val: str | None) -> int | None:
    """Parse a Scryfall price string into integer cents.

    Uses Decimal + ROUND_HALF_UP rather than round(float(val) * 100):
    Python's round() on floats is banker's rounding (round-half-to-even),
    which silently mishandles cases like round(0.5) == 0 - "$0.005"
    becoming 0 cents instead of 1.
    """
    if val is None:
        return None
    s = str(val).strip()
    if not s or s.lower() in _INVALID_PRICE_SENTINELS:
        return None
    try:
        d = Decimal(s)
    except InvalidOperation:
        return None
    if d < 0:
        return None
    cents = (d * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    return int(cents)


def _card_to_row(c: dict) -> dict:
    return {
        "id": c["id"],
        "name": c["name"],
        "set_code": c["set"],
        "set_name": c["set_name"],
        "collector_number": c["collector_number"],
        "mana_cost": c.get("mana_cost"),
        # math.ceil, not round(): round() is banker's rounding, so
        # round(0.5) == 0 silently drops half-cost cards (e.g. Little Girl,
        # cmc=0.5) to cmc=0. Half-cost cards round up.
        "cmc": math.ceil(c.get("cmc") or 0),
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
        values = [_card_to_row(c) for c in batch]
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
