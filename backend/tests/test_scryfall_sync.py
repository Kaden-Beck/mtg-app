"""Tests for app/services/scryfall_sync.py.

Strategy:
- _price_cents and _card_to_row are pure functions; tested directly.
- sync_scryfall_bulk: httpx is mocked (no network), db is an AsyncMock (no DB writes).
- Celery task: AsyncSessionLocal and sync_scryfall_bulk are mocked.

No real database is required; no Scryfall endpoints are contacted.
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, call, patch

from app.services.scryfall_sync import (
    BULK_META_URL,
    _card_to_row,
    _price_cents,
    sync_scryfall_bulk,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

FAKE_DOWNLOAD_URL = "https://fake-scryfall.test/bulk/default-cards.json"

FAKE_META = {"download_uri": FAKE_DOWNLOAD_URL}


def make_card(
    *,
    id: str = "aabb-1234",
    name: str = "Lightning Bolt",
    set_code: str = "m11",
    set_name: str = "Magic 2011",
    collector_number: str = "149",
    rarity: str = "common",
    **overrides,
) -> dict:
    """Minimal fake Scryfall card dict with sensible defaults."""
    card: dict = {
        "id": id,
        "name": name,
        "set": set_code,
        "set_name": set_name,
        "collector_number": collector_number,
        "rarity": rarity,
        "cmc": 1.0,
        "type_line": "Instant",
        "color_identity": ["R"],
        "prices": {"usd": "0.25", "usd_foil": "1.50", "eur": "0.20"},
    }
    card.update(overrides)
    return card


def make_httpx_mock(cards: list[dict]) -> MagicMock:
    """Build a mock for httpx.AsyncClient that returns fake bulk data."""
    meta_resp = MagicMock()
    meta_resp.json.return_value = FAKE_META

    cards_resp = MagicMock()
    cards_resp.json.return_value = cards

    mock_client = AsyncMock()
    mock_client.get.side_effect = [meta_resp, cards_resp]

    mock_cls = MagicMock()
    mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
    mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)
    return mock_cls


# ---------------------------------------------------------------------------
# _price_cents
# ---------------------------------------------------------------------------


class TestPriceCents:
    def test_normal_value(self) -> None:
        assert _price_cents("1.25") == 125

    def test_whole_dollar(self) -> None:
        assert _price_cents("10.00") == 1000

    def test_zero(self) -> None:
        assert _price_cents("0.00") == 0

    def test_rounds_half_up(self) -> None:
        # 0.995 → 99.5 cents → rounds to 100
        assert _price_cents("0.995") == 100

    def test_none_input(self) -> None:
        assert _price_cents(None) is None

    def test_invalid_string(self) -> None:
        assert _price_cents("N/A") is None

    def test_empty_string(self) -> None:
        assert _price_cents("") is None


# ---------------------------------------------------------------------------
# _card_to_row
# ---------------------------------------------------------------------------


class TestCardToRow:
    def test_required_fields(self) -> None:
        c = make_card()
        row = _card_to_row(c)
        assert row["id"] == "aabb-1234"
        assert row["name"] == "Lightning Bolt"
        assert row["set_code"] == "m11"
        assert row["set_name"] == "Magic 2011"
        assert row["collector_number"] == "149"
        assert row["rarity"] == "common"

    def test_set_code_uses_set_key(self) -> None:
        # Scryfall uses "set" not "set_code" as the key in the raw payload
        c = make_card(set_code="lea")
        assert _card_to_row(c)["set_code"] == "lea"

    def test_price_usd_converted_to_cents(self) -> None:
        c = make_card(prices={"usd": "2.50", "usd_foil": None, "eur": None})
        row = _card_to_row(c)
        assert row["price_usd"] == 250
        assert row["price_usd_foil"] is None
        assert row["price_eur"] is None

    def test_prices_missing_key(self) -> None:
        c = make_card()
        del c["prices"]
        row = _card_to_row(c)
        assert row["price_usd"] is None
        assert row["price_usd_foil"] is None
        assert row["price_eur"] is None

    def test_cmc_rounded_to_int(self) -> None:
        c = make_card(cmc=3.0)
        assert _card_to_row(c)["cmc"] == 3

    def test_cmc_none_defaults_to_zero(self) -> None:
        c = make_card(cmc=None)
        assert _card_to_row(c)["cmc"] == 0

    def test_color_identity_default(self) -> None:
        c = make_card()
        del c["color_identity"]
        assert _card_to_row(c)["color_identity"] == []

    def test_type_line_default(self) -> None:
        c = make_card()
        del c["type_line"]
        assert _card_to_row(c)["type_line"] == ""

    def test_optional_fields_missing(self) -> None:
        c = make_card()
        row = _card_to_row(c)
        assert row["mana_cost"] is None
        assert row["oracle_text"] is None
        assert row["image_uris"] is None
        assert row["legalities"] is None

    def test_scryfall_data_is_full_raw_card(self) -> None:
        c = make_card()
        row = _card_to_row(c)
        assert row["scryfall_data"] is c


# ---------------------------------------------------------------------------
# sync_scryfall_bulk — HTTP behaviour
# ---------------------------------------------------------------------------


class TestSyncScryfallBulkHTTP:
    def _run(self, cards: list[dict]) -> tuple[MagicMock, int]:
        mock_cls = make_httpx_mock(cards)
        mock_db = AsyncMock()
        with patch("app.services.scryfall_sync.httpx.AsyncClient", mock_cls):
            count = asyncio.run(sync_scryfall_bulk(mock_db))
        return mock_cls, count

    def test_fetches_meta_url_first(self) -> None:
        mock_cls, _ = self._run([make_card()])
        client = mock_cls.return_value.__aenter__.return_value
        assert client.get.call_args_list[0] == call(BULK_META_URL)

    def test_fetches_download_url_from_meta(self) -> None:
        mock_cls, _ = self._run([make_card()])
        client = mock_cls.return_value.__aenter__.return_value
        assert client.get.call_args_list[1] == call(FAKE_DOWNLOAD_URL)

    def test_returns_total_card_count(self) -> None:
        cards = [make_card(id=f"id-{i}") for i in range(5)]
        _, count = self._run(cards)
        assert count == 5

    def test_empty_bulk_returns_zero(self) -> None:
        _, count = self._run([])
        assert count == 0


# ---------------------------------------------------------------------------
# sync_scryfall_bulk — DB write behaviour
# ---------------------------------------------------------------------------


class TestSyncScryfallBulkDB:
    def _run_with_db(self, cards: list[dict]) -> AsyncMock:
        mock_cls = make_httpx_mock(cards)
        mock_db = AsyncMock()
        with patch("app.services.scryfall_sync.httpx.AsyncClient", mock_cls):
            asyncio.run(sync_scryfall_bulk(mock_db))
        return mock_db

    def test_single_batch_one_execute_and_commit(self) -> None:
        cards = [make_card(id=f"id-{i}") for i in range(10)]
        mock_db = self._run_with_db(cards)
        assert mock_db.execute.call_count == 1
        assert mock_db.commit.call_count == 1

    def test_two_batches_for_501_cards(self) -> None:
        # BATCH=500; 501 cards → 2 batches → 2 execute + 2 commit calls
        cards = [make_card(id=f"id-{i}") for i in range(501)]
        mock_db = self._run_with_db(cards)
        assert mock_db.execute.call_count == 2
        assert mock_db.commit.call_count == 2

    def test_exactly_500_cards_is_one_batch(self) -> None:
        cards = [make_card(id=f"id-{i}") for i in range(500)]
        mock_db = self._run_with_db(cards)
        assert mock_db.execute.call_count == 1

    def test_empty_input_no_db_calls(self) -> None:
        mock_db = self._run_with_db([])
        mock_db.execute.assert_not_called()
        mock_db.commit.assert_not_called()


# ---------------------------------------------------------------------------
# Celery task
# ---------------------------------------------------------------------------


class TestCeleryTask:
    def test_task_calls_sync_with_db_session(self) -> None:
        from app.tasks.tasks import scryfall_sync_task

        mock_db = AsyncMock()
        mock_db.__aenter__ = AsyncMock(return_value=mock_db)
        mock_db.__aexit__ = AsyncMock(return_value=False)

        with patch("app.tasks.tasks.AsyncSessionLocal", return_value=mock_db), patch(
            "app.tasks.tasks.sync_scryfall_bulk", new=AsyncMock(return_value=0)
        ) as mock_sync:
            scryfall_sync_task()

        mock_sync.assert_called_once_with(mock_db)
