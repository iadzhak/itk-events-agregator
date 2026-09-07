import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.background_tasks import periodic_sync_meta
from app.core import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(periodic_sync_meta(settings.update_interval_h))
    yield
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass
