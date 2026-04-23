import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db import AsyncSessionLocal
from app.services.scryfall_sync import sync_scryfall_bulk


async def main():
    """One time seed script"""
    async with AsyncSessionLocal() as db:
        count = await sync_scryfall_bulk(db)
        print(f"Synced {count} cards.")


asyncio.run(main())
