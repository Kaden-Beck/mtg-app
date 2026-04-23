import csv
import io
from dataclasses import dataclass
from typing import Literal

from sqlalchemy import select, tuple_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import Card

CardCondition = Literal["NM", "LP", "MP", "HP", "DMG"]


@dataclass
class CanonicalCard:
    scryfall_id: str
    quantity: int
    foil: bool
    condition: CardCondition
    language: str
    purchase_price: float | None = None


MANABOX_TO_CANONICAL: dict[str, CardCondition] = {
    "near_mint": "NM",
    "lightly_played": "LP",
    "moderately_played": "MP",
    "heavily_played": "HP",
    "damaged": "DMG",
}
CANONICAL_TO_MANABOX = {v: k for k, v in MANABOX_TO_CANONICAL.items()}


def from_manabox(csv_text: str) -> list[CanonicalCard]:
    reader = csv.DictReader(io.StringIO(csv_text))
    cards = []
    for row in reader:
        raw_condition = row.get("Condition", "").lower().replace(" ", "_")
        raw_price = row.get("Purchase price") or row.get("Purchase Price")
        cards.append(
            CanonicalCard(
                scryfall_id=row["Scryfall ID"],
                quantity=int(row.get("Quantity", 1) or 1),
                foil=row.get("Foil", "").lower() == "foil",
                condition=MANABOX_TO_CANONICAL.get(raw_condition, "NM"),
                language=row.get("Language", "en") or "en",
                purchase_price=float(raw_price) if raw_price else None,
            )
        )
    return cards


def to_manabox(cards: list[CanonicalCard]) -> str:
    fieldnames = [
        "Scryfall ID",
        "Quantity",
        "Foil",
        "Condition",
        "Language",
        "Purchase Price",
    ]
    out = io.StringIO()
    writer = csv.DictWriter(out, fieldnames=fieldnames)
    writer.writeheader()
    for c in cards:
        writer.writerow(
            {
                "Scryfall ID": c.scryfall_id,
                "Quantity": c.quantity,
                "Foil": "foil" if c.foil else "",
                "Condition": CANONICAL_TO_MANABOX.get(c.condition, "Near Mint"),
                "Language": c.language,
                "Purchase Price": str(c.purchase_price) if c.purchase_price else "",
            }
        )
    return out.getvalue()


MOXFIELD_CONDITION_MAP: dict[str, CardCondition] = {
    "NM": "NM",
    "LP": "LP",
    "MP": "MP",
    "HP": "HP",
    "DMG": "DMG",
}

MOXFIELD_LANGUAGE_MAP: dict[str, str] = {
    "English": "en",
    "French": "fr",
    "German": "de",
    "Italian": "it",
    "Japanese": "ja",
    "Korean": "ko",
    "Portuguese": "pt",
    "Russian": "ru",
    "Simplified Chinese": "zhs",
    "Spanish": "es",
    "Traditional Chinese": "zht",
}
CANONICAL_TO_MOXFIELD_LANGUAGE = {v: k for k, v in MOXFIELD_LANGUAGE_MAP.items()}


async def from_moxfield(csv_text: str, db: AsyncSession) -> list[CanonicalCard]:
    rows = list(csv.DictReader(io.StringIO(csv_text)))

    pairs = {(row["Edition"], row["Collector Number"]) for row in rows}
    result = await db.execute(
        select(Card.id, Card.set_code, Card.collector_number).where(
            tuple_(Card.set_code, Card.collector_number).in_(pairs)
        )
    )
    lookup: dict[tuple[str, str], str] = {
        (r.set_code, r.collector_number): r.id for r in result
    }

    cards = []
    for row in rows:
        scryfall_id = lookup.get((row["Edition"], row["Collector Number"]))
        if scryfall_id is None:
            continue
        raw_lang = row.get("Language", "") or ""
        cards.append(
            CanonicalCard(
                scryfall_id=scryfall_id,
                quantity=int(row.get("Count", 1) or 1),
                foil=row.get("Foil", "").lower() in ("foil", "etched"),
                condition=MOXFIELD_CONDITION_MAP.get(row.get("Condition", "NM"), "NM"),
                language=MOXFIELD_LANGUAGE_MAP.get(raw_lang, "en"),
            )
        )
    return cards


def to_moxfield(cards: list[CanonicalCard]) -> str:
    fieldnames = ["Count", "Scryfall ID", "Condition", "Foil", "Language"]
    out = io.StringIO()
    writer = csv.DictWriter(out, fieldnames=fieldnames)
    writer.writeheader()
    for c in cards:
        writer.writerow(
            {
                "Count": c.quantity,
                "Scryfall ID": c.scryfall_id,
                "Condition": c.condition,
                "Foil": "foil" if c.foil else "",
                "Language": CANONICAL_TO_MOXFIELD_LANGUAGE.get(c.language, "English"),
            }
        )
    return out.getvalue()


def from_archidekt(csv_text: str) -> list[CanonicalCard]:
    reader = csv.DictReader(io.StringIO(csv_text))
    cards = []
    for row in reader:
        scryfall_id = row["scryfall_uuid"]
        condition = MOXFIELD_CONDITION_MAP.get(row.get("condition", "NM"), "NM")
        language = row.get("lang", "en") or "en"

        qty = int(row.get("quantity", 0) or 0)
        foil_qty = int(row.get("foil_quantity", 0) or 0)

        if qty > 0:
            cards.append(
                CanonicalCard(
                    scryfall_id=scryfall_id,
                    quantity=qty,
                    foil=False,
                    condition=condition,
                    language=language,
                )
            )
        if foil_qty > 0:
            cards.append(
                CanonicalCard(
                    scryfall_id=scryfall_id,
                    quantity=foil_qty,
                    foil=True,
                    condition=condition,
                    language=language,
                )
            )
    return cards


def to_archidekt(cards: list[CanonicalCard]) -> str:
    fieldnames = ["scryfall_uuid", "quantity", "foil_quantity", "condition", "lang"]
    out = io.StringIO()
    writer = csv.DictWriter(out, fieldnames=fieldnames)
    writer.writeheader()
    for c in cards:
        writer.writerow(
            {
                "scryfall_uuid": c.scryfall_id,
                "quantity": c.quantity if not c.foil else 0,
                "foil_quantity": c.quantity if c.foil else 0,
                "condition": c.condition,
                "lang": c.language,
            }
        )
    return out.getvalue()


CollectionFormat = Literal["manabox", "moxfield", "archidekt"]

SYNC_FROM_ADAPTERS = {
    "manabox": from_manabox,
    "archidekt": from_archidekt,
}
TO_ADAPTERS = {
    "manabox": to_manabox,
    "moxfield": to_moxfield,
    "archidekt": to_archidekt,
}


async def convert(
    csv_text: str,
    from_fmt: CollectionFormat,
    to_fmt: CollectionFormat,
    db: AsyncSession | None = None,
) -> tuple[str, int]:
    if from_fmt == "moxfield":
        if db is None:
            raise ValueError("db session is required for moxfield import")
        canonical = await from_moxfield(csv_text, db)
    else:
        canonical = SYNC_FROM_ADAPTERS[from_fmt](csv_text)
    output = TO_ADAPTERS[to_fmt](canonical)
    return output, len(canonical)
