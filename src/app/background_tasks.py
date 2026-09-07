import asyncio
import datetime as dt

from app.clients import EventsProviderClient
from app.core import get_logger, settings
from app.core.db import AsyncSessionLocal
from app.dependencies import get_sync_service
from app.repository import EventRepository, PlaceRepository, SyncRepository
from app.utils import EventsPaginator

logger = get_logger(__name__)


async def sync_meta_once():
    async with AsyncSessionLocal() as session:
        client = EventsProviderClient(
            base_url=settings.provider_base_url,
            api_key=settings.provider_api_key,
            retries=settings.provider_retries,
        )
        service = get_sync_service(
            client=client,
            paginator_class=EventsPaginator,
            sync_repo=SyncRepository(session),
            events_repo=EventRepository(session),
            place_repo=PlaceRepository(session),
        )
        last_sync_time = await service.run(session)
        await client.aclose()
        return last_sync_time


async def periodic_sync_meta(period_h: int):
    while True:
        try:
            last_sync_time = await sync_meta_once()
            next_sync_time = last_sync_time + dt.timedelta(hours=period_h)
            now = dt.datetime.now(tz=dt.UTC)
            delta = next_sync_time - now
            logger.info(
                f'Следующая синхронизация запанирована на {next_sync_time!s}'
            )
            await asyncio.sleep(delta.total_seconds())
        except asyncio.CancelledError:
            break
