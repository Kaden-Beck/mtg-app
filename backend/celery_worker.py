import os
from celery import Celery


REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")


celery_app = Celery(
    "mtg", broker=REDIS_URL, backend=REDIS_URL, include=["app.tasks.tasks"]
)


celery_app.conf.beat_schedule = {
    "scryfall-sync-daily": {
        "task": "app.tasks.tasks.scryfall_sync_task",
        "schedule": 3600 * 24,  # every 24h
    },
    "price-snapshot-daily": {
        "task": "app.tasks.tasks.price_snapshot_task",
        "schedule": 3600 * 24,
    },
}
celery_app.conf.update(
    timezone="UTC",
    broker_connection_retry_on_startup=True,
)
