import asyncio
from celery_worker import celery_app
from app.db import AsyncSessionLocal
from app.services.scryfall_sync import sync_scryfall_bulk
from app.services.price_snapshot import take_price_snapshot


@celery_app.task(name="app.tasks.tasks.scryfall_sync_task")
def scryfall_sync_task():
    async def _run():
        async with AsyncSessionLocal() as db:
            await sync_scryfall_bulk(db)

    asyncio.run(_run())


@celery_app.task(name="app.tasks.tasks.price_snapshot_task")
def price_snapshot_task():
    async def _run():
        async with AsyncSessionLocal() as db:
            await take_price_snapshot(db)

    asyncio.run(_run())
