import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.background_tasks import periodic_sync_meta
from app.core import settings
from app.core.db import AsyncSessionLocal
from app.repository import OutboxRepository
from app.workers import OutboxWorker


@asynccontextmanager
async def lifespan(app: FastAPI):
    outbox_worker = OutboxWorker(
        polling_interval_s=settings.polling_interval_s,
        max_retries=settings.max_retries,
        outbox_repo_cls=OutboxRepository,
        session_factory=AsyncSessionLocal,
    )
    tasks = [
        asyncio.create_task(periodic_sync_meta(settings.update_interval_h)),
        asyncio.create_task(outbox_worker.run()),
    ]
    yield
    for task in tasks:
        task.cancel()
    try:
        for task in tasks:
            await task
    except asyncio.CancelledError:
        pass
