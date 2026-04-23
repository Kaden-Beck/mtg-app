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

import pytest

from app.services.converter import (
    CanonicalCard,
    convert,
    from_archidekt,
    from_manabox,
    to_archidekt,
    to_moxfield,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

MANABOX_CSV = """\
Binder Name,Binder Type,Name,Set code,Set name,Collector number,Foil,Rarity,Quantity,ManaBox ID,Scryfall ID,Purchase price,Misprint,Altered,Condition,Language,Purchase price currency
Main,Collection,Lightning Bolt,m11,Magic 2011,149,normal,common,2,11111111,a20c5a55-1e8b-4f92-b6f1-e7e1a8a1b4d3,0.50,False,False,near_mint,English,USD
Main,Collection,Brainstorm,ice,Ice Age,48,foil,common,1,22222222,84128e98-87d4-4b69-9d95-7a6a8f99e9cd,1.25,False,False,lightly_played,Japanese,USD
Main,Collection,Dark Ritual,lea,Limited Edition Alpha,74,normal,common,1,33333333,b47c77c8-9b3c-4e0d-8e4a-5e6b3e9b4f2e,,False,False,heavily_played,English,USD
"""

ARCHIDEKT_CSV = """\
scryfall_uuid,quantity,foil_quantity,condition,lang
a20c5a55-1e8b-4f92-b6f1-e7e1a8a1b4d3,3,1,NM,en
84128e98-87d4-4b69-9d95-7a6a8f99e9cd,0,2,LP,ja
"""


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
        moxfield_csv = "Count,Tradelist Count,Name,Edition,Condition,Language,Foil,Tags,Last Modified,Collector Number,Alter,Proxy,Purchase Price\n1,0,Lightning Bolt,m11,NM,English,,,,149,False,False,\n"
        with pytest.raises(ValueError, match="db session is required"):
            asyncio.run(convert(moxfield_csv, "moxfield", "manabox", db=None))
