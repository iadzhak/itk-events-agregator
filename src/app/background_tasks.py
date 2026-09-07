from app.core.db import AsyncSessionLocal
from app.dependencies import (
    get_event_repository,
    get_events_provider_client,
    get_place_repository,
    get_sync_repository,
    get_sync_service,
)
from app.utils import EventsPaginator


async def sync_meta_once():
    async with AsyncSessionLocal() as session:
        service = get_sync_service(
            client=get_events_provider_client(),
            paginator_class=EventsPaginator,
            sync_repo=get_sync_repository(session),
            events_repo=get_event_repository(session),
            place_repo=get_place_repository(session)
        )
        await service.run(session)
