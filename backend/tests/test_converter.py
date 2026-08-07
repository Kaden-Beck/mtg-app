"""Tests for app/services/converter.py.

Covers:
    - from_manabox: condition mapping, foil, purchase price, language
    - from_archidekt: split foil/non-foil rows, column names
    - to_moxfield / to_archidekt: round-trip field correctness
    - convert(): manabox→moxfield end-to-end (no DB needed; manabox carries scryfall_id)
"""

import asyncio
import csv
import io
from types import SimpleNamespace

import pytest

from app.services.converter import (
    CanonicalCard,
    convert,
    from_archidekt,
    from_manabox,
    from_moxfield,
    to_archidekt,
    to_manabox,
    to_moxfield,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

MANABOX_CSV = (
    "Binder Name,Binder Type,Name,Set code,Set name,Collector number,Foil,"
    "Rarity,Quantity,ManaBox ID,Scryfall ID,Purchase price,Misprint,Altered,"
    "Condition,Language,Purchase price currency\n"
    "Main,Collection,Lightning Bolt,m11,Magic 2011,149,normal,common,2,"
    "11111111,a20c5a55-1e8b-4f92-b6f1-e7e1a8a1b4d3,0.50,False,False,"
    "near_mint,English,USD\n"
    "Main,Collection,Brainstorm,ice,Ice Age,48,foil,common,1,22222222,"
    "84128e98-87d4-4b69-9d95-7a6a8f99e9cd,1.25,False,False,lightly_played,"
    "Japanese,USD\n"
    "Main,Collection,Dark Ritual,lea,Limited Edition Alpha,74,normal,common,1,"
    "33333333,b47c77c8-9b3c-4e0d-8e4a-5e6b3e9b4f2e,,False,False,"
    "heavily_played,English,USD\n"
)

ARCHIDEKT_CSV = """\
scryfall_uuid,quantity,foil_quantity,condition,lang
a20c5a55-1e8b-4f92-b6f1-e7e1a8a1b4d3,3,1,NM,en
84128e98-87d4-4b69-9d95-7a6a8f99e9cd,0,2,LP,ja
"""


class _StubDb:
    """Minimal stand-in for AsyncSession.execute() in from_moxfield tests.

    Phase B is pure-unit (no DB, no event loop beyond asyncio.run). This
    fakes just enough of the (set_code, collector_number) -> scryfall_id
    lookup shape from_moxfield expects, without touching a real database.
    """

    def __init__(self, *, scryfall_id: str, set_code: str, collector_number: str) -> None:
        self._row = SimpleNamespace(
            id=scryfall_id, set_code=set_code, collector_number=collector_number
        )

    async def execute(self, *_args, **_kwargs):
        return [self._row]


# ---------------------------------------------------------------------------
# from_manabox
# ---------------------------------------------------------------------------


class TestFromManabox:
    def test_parses_row_count(self) -> None:
        cards = from_manabox(MANABOX_CSV)
        assert len(cards) == 3

    def test_scryfall_id(self) -> None:
        cards = from_manabox(MANABOX_CSV)
        assert cards[0].scryfall_id == "a20c5a55-1e8b-4f92-b6f1-e7e1a8a1b4d3"

    def test_quantity(self) -> None:
        cards = from_manabox(MANABOX_CSV)
        assert cards[0].quantity == 2
        assert cards[1].quantity == 1

    def test_foil_detection(self) -> None:
        cards = from_manabox(MANABOX_CSV)
        assert cards[0].foil is False  # "normal"
        assert cards[1].foil is True  # "foil"

    def test_condition_snake_case(self) -> None:
        cards = from_manabox(MANABOX_CSV)
        assert cards[0].condition == "NM"  # near_mint
        assert cards[1].condition == "LP"  # lightly_played
        assert cards[2].condition == "HP"  # heavily_played

    def test_language_passthrough(self) -> None:
        cards = from_manabox(MANABOX_CSV)
        assert cards[0].language == "English"
        assert cards[1].language == "Japanese"

    def test_purchase_price_parsed(self) -> None:
        cards = from_manabox(MANABOX_CSV)
        assert cards[0].purchase_price == pytest.approx(0.50)
        assert cards[1].purchase_price == pytest.approx(1.25)

    def test_purchase_price_empty_is_none(self) -> None:
        cards = from_manabox(MANABOX_CSV)
        assert cards[2].purchase_price is None


# ---------------------------------------------------------------------------
# from_archidekt
# ---------------------------------------------------------------------------


class TestFromArchidekt:
    def test_splits_foil_and_nonfoil(self) -> None:
        # row 1: qty=3, foil_qty=1 → 2 CanonicalCards
        # row 2: qty=0, foil_qty=2 → 1 CanonicalCard (foil only)
        cards = from_archidekt(ARCHIDEKT_CSV)
        assert len(cards) == 3

    def test_nonfoil_row(self) -> None:
        cards = from_archidekt(ARCHIDEKT_CSV)
        non_foil = [c for c in cards if not c.foil]
        assert len(non_foil) == 1
        assert non_foil[0].quantity == 3
        assert non_foil[0].scryfall_id == "a20c5a55-1e8b-4f92-b6f1-e7e1a8a1b4d3"

    def test_foil_rows(self) -> None:
        cards = from_archidekt(ARCHIDEKT_CSV)
        foil = [c for c in cards if c.foil]
        assert len(foil) == 2
        quantities = {c.scryfall_id: c.quantity for c in foil}
        assert quantities["a20c5a55-1e8b-4f92-b6f1-e7e1a8a1b4d3"] == 1
        assert quantities["84128e98-87d4-4b69-9d95-7a6a8f99e9cd"] == 2

    def test_language_column(self) -> None:
        cards = from_archidekt(ARCHIDEKT_CSV)
        by_id = {c.scryfall_id: c for c in cards}
        assert by_id["a20c5a55-1e8b-4f92-b6f1-e7e1a8a1b4d3"].language == "en"
        assert by_id["84128e98-87d4-4b69-9d95-7a6a8f99e9cd"].language == "ja"

    def test_condition_mapping(self) -> None:
        cards = from_archidekt(ARCHIDEKT_CSV)
        assert cards[0].condition == "NM"


# ---------------------------------------------------------------------------
# to_moxfield
# ---------------------------------------------------------------------------


class TestToMoxfield:
    def test_roundtrip_scryfall_id_and_count(self) -> None:
        cards = [
            CanonicalCard(
                scryfall_id="abc-123",
                quantity=2,
                foil=False,
                condition="NM",
                language="en",
            )
        ]
        output = to_moxfield(cards)
        reader = list(csv.DictReader(io.StringIO(output)))
        assert len(reader) == 1
        assert reader[0]["Scryfall ID"] == "abc-123"
        assert reader[0]["Count"] == "2"

    def test_foil_field(self) -> None:
        cards = [
            CanonicalCard(
                scryfall_id="x", quantity=1, foil=True, condition="NM", language="en"
            ),
            CanonicalCard(
                scryfall_id="y", quantity=1, foil=False, condition="NM", language="en"
            ),
        ]
        rows = list(csv.DictReader(io.StringIO(to_moxfield(cards))))
        assert rows[0]["Foil"] == "foil"
        assert rows[1]["Foil"] == ""

    def test_language_mapped_to_full_name(self) -> None:
        cards = [
            CanonicalCard(
                scryfall_id="x", quantity=1, foil=False, condition="NM", language="ja"
            )
        ]
        rows = list(csv.DictReader(io.StringIO(to_moxfield(cards))))
        assert rows[0]["Language"] == "Japanese"


# ---------------------------------------------------------------------------
# to_manabox
# ---------------------------------------------------------------------------


class TestToManabox:
    def test_roundtrip_scryfall_id_and_quantity(self) -> None:
        cards = [
            CanonicalCard(
                scryfall_id="abc-123",
                quantity=4,
                foil=False,
                condition="NM",
                language="English",
            )
        ]
        rows = list(csv.DictReader(io.StringIO(to_manabox(cards))))
        assert len(rows) == 1
        assert rows[0]["Scryfall ID"] == "abc-123"
        assert rows[0]["Quantity"] == "4"

    def test_foil_field(self) -> None:
        cards = [
            CanonicalCard(
                scryfall_id="x", quantity=1, foil=True, condition="NM", language="English"
            ),
            CanonicalCard(
                scryfall_id="y", quantity=1, foil=False, condition="NM", language="English"
            ),
        ]
        rows = list(csv.DictReader(io.StringIO(to_manabox(cards))))
        assert rows[0]["Foil"] == "foil"
        assert rows[1]["Foil"] == ""

    def test_condition_mapped_to_snake_case(self) -> None:
        cards = [
            CanonicalCard(
                scryfall_id="x", quantity=1, foil=False, condition="LP", language="English"
            )
        ]
        rows = list(csv.DictReader(io.StringIO(to_manabox(cards))))
        assert rows[0]["Condition"] == "lightly_played"


# ---------------------------------------------------------------------------
# to_archidekt
# ---------------------------------------------------------------------------


class TestToArchidekt:
    def test_foil_quantity_split(self) -> None:
        cards = [
            CanonicalCard(
                scryfall_id="abc", quantity=3, foil=False, condition="NM", language="en"
            ),
            CanonicalCard(
                scryfall_id="abc", quantity=1, foil=True, condition="NM", language="en"
            ),
        ]
        rows = list(csv.DictReader(io.StringIO(to_archidekt(cards))))
        assert len(rows) == 2
        non_foil_row = rows[0]
        foil_row = rows[1]
        assert non_foil_row["quantity"] == "3"
        assert non_foil_row["foil_quantity"] == "0"
        assert foil_row["quantity"] == "0"
        assert foil_row["foil_quantity"] == "1"


# ---------------------------------------------------------------------------
# convert() — manabox → moxfield end-to-end
# ---------------------------------------------------------------------------


class TestConvertManaboxToMoxfield:
    def test_returns_correct_count(self) -> None:
        _, count = asyncio.run(convert(MANABOX_CSV, "manabox", "moxfield"))
        assert count == 3

    def test_output_is_valid_csv(self) -> None:
        output, _ = asyncio.run(convert(MANABOX_CSV, "manabox", "moxfield"))
        rows = list(csv.DictReader(io.StringIO(output)))
        assert len(rows) == 3

    def test_scryfall_ids_preserved(self) -> None:
        output, _ = asyncio.run(convert(MANABOX_CSV, "manabox", "moxfield"))
        rows = list(csv.DictReader(io.StringIO(output)))
        ids = {r["Scryfall ID"] for r in rows}
        assert "a20c5a55-1e8b-4f92-b6f1-e7e1a8a1b4d3" in ids
        assert "84128e98-87d4-4b69-9d95-7a6a8f99e9cd" in ids

    def test_foil_card_marked(self) -> None:
        output, _ = asyncio.run(convert(MANABOX_CSV, "manabox", "moxfield"))
        rows = list(csv.DictReader(io.StringIO(output)))
        brainstorm = next(
            r
            for r in rows
            if r["Scryfall ID"] == "84128e98-87d4-4b69-9d95-7a6a8f99e9cd"
        )
        assert brainstorm["Foil"] == "foil"

    def test_moxfield_requires_db_raises(self) -> None:
        moxfield_csv = (
            "Count,Tradelist Count,Name,Edition,Condition,Language,Foil,Tags,"
            "Last Modified,Collector Number,Alter,Proxy,Purchase Price\n"
            "1,0,Lightning Bolt,m11,NM,English,,,,149,False,False,\n"
        )
        with pytest.raises(ValueError, match="db session is required"):
            asyncio.run(convert(moxfield_csv, "moxfield", "manabox", db=None))


# ---------------------------------------------------------------------------
# Bug 3 (gap): edge cases the happy-path tests above don't cover
# ---------------------------------------------------------------------------


class TestConverterEdgeCases:
    def test_manabox_handles_utf8_bom(self) -> None:
        """Real Manabox exports include a UTF-8 BOM before the header row."""
        csv_with_bom = (
            "﻿Binder Name,Binder Type,Name,Set code,Set name,Collector number,"
            "Foil,Rarity,Quantity,ManaBox ID,Scryfall ID,Purchase price,Misprint,"
            "Altered,Condition,Language,Purchase price currency\n"
            "Main,Collection,Lightning Bolt,m11,Magic 2011,149,normal,common,4,"
            "11111111,abc-123,,False,False,near_mint,English,USD\n"
        )
        cards = from_manabox(csv_with_bom)
        assert len(cards) == 1
        assert cards[0].scryfall_id == "abc-123"

    def test_archidekt_old_export_missing_scryfall_id_raises(self) -> None:
        """Older Archidekt exports omit the scryfall_uuid column entirely.

        Design decision: raise clearly rather than silently drop the card
        or KeyError with no context. A DB-backed (name, set) fallback is
        deliberately out of scope here - from_archidekt is a pure, no-DB
        function by design (see convert(), which only reaches into the DB
        for moxfield imports); a fallback lookup belongs in a later,
        DB-touching phase if it's ever wanted.
        """
        csv_without_id = "name,quantity,setCode,foil,condition\nLightning Bolt,4,M11,false,NM\n"
        with pytest.raises(ValueError, match="scryfall_uuid"):
            from_archidekt(csv_without_id)

    @pytest.mark.parametrize("foil_value", ["Foil", "FOIL", "foil", ""])
    def test_manabox_foil_casing_variations(self, foil_value: str) -> None:
        csv_text = (
            "Name,Set code,Set name,Collector number,Foil,Rarity,Quantity,"
            "Scryfall ID,Condition,Language\n"
            f"Lightning Bolt,m11,Magic 2011,149,{foil_value},common,1,abc-123,near_mint,English\n"
        )
        cards = from_manabox(csv_text)
        assert cards[0].foil == (foil_value.lower() == "foil")

    @pytest.mark.parametrize("foil_value", ["foil", "etched", "Foil", "ETCHED", ""])
    def test_moxfield_foil_casing_variations(self, foil_value: str) -> None:
        moxfield_csv = (
            "Count,Tradelist Count,Name,Edition,Condition,Language,Foil,Tags,"
            "Last Modified,Collector Number,Alter,Proxy,Purchase Price\n"
            f"1,0,Lightning Bolt,m11,NM,English,{foil_value},,,149,False,False,\n"
        )
        db = _StubDb(scryfall_id="abc-123", set_code="m11", collector_number="149")
        cards = asyncio.run(from_moxfield(moxfield_csv, db))
        assert cards[0].foil == (foil_value.lower() in ("foil", "etched"))

    def test_round_trip_manabox_to_moxfield_preserves_scryfall_id(self) -> None:
        cards_in = from_manabox(MANABOX_CSV)
        moxfield_csv = to_moxfield(cards_in)
        rows = list(csv.DictReader(io.StringIO(moxfield_csv)))
        ids_in = {c.scryfall_id for c in cards_in}
        ids_out = {r["Scryfall ID"] for r in rows}
        assert ids_in == ids_out

    def test_moxfield_row_skipped_when_not_in_cards_table(self) -> None:
        """Edition/Collector Number that don't match any row DB returned are dropped."""
        moxfield_csv = (
            "Count,Tradelist Count,Name,Edition,Condition,Language,Foil,Tags,"
            "Last Modified,Collector Number,Alter,Proxy,Purchase Price\n"
            "1,0,Unknown Card,zzz,NM,English,,,,999,False,False,\n"
        )
        db = _StubDb(scryfall_id="abc-123", set_code="m11", collector_number="149")
        cards = asyncio.run(from_moxfield(moxfield_csv, db))
        assert cards == []

    def test_convert_moxfield_to_archidekt_end_to_end(self) -> None:
        moxfield_csv = (
            "Count,Tradelist Count,Name,Edition,Condition,Language,Foil,Tags,"
            "Last Modified,Collector Number,Alter,Proxy,Purchase Price\n"
            "3,0,Lightning Bolt,m11,NM,English,,,,149,False,False,\n"
        )
        db = _StubDb(scryfall_id="abc-123", set_code="m11", collector_number="149")
        output, count = asyncio.run(convert(moxfield_csv, "moxfield", "archidekt", db=db))
        assert count == 1
        rows = list(csv.DictReader(io.StringIO(output)))
        assert rows[0]["scryfall_uuid"] == "abc-123"
        assert rows[0]["quantity"] == "3"
