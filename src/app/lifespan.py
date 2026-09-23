import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.background_tasks import periodic_sync_meta
from app.clients import CapashinoClient
from app.core import settings
from app.core.db import AsyncSessionLocal
from app.repository import OutboxRepository
from app.types import OutboxType
from app.workers import OutboxWorker
from app.workers.handlers import EventRegistrationHandler


@asynccontextmanager
async def lifespan(app: FastAPI):
    outbox_worker = OutboxWorker(
        polling_interval_s=settings.polling_interval_s,
        max_retries=settings.max_retries,
        outbox_repo_cls=OutboxRepository,
        session_factory=AsyncSessionLocal,
    )
    capashino = CapashinoClient(
        base_url=settings.capashino_base_url,
        api_key=settings.capashino_api_key,
        retries=settings.capashino_retries,
    )
    reg_handler = EventRegistrationHandler(capashino)
    outbox_worker.register_handler(OutboxType.EVENT_REGISTRATION, reg_handler)
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
    await capashino.aclose()
