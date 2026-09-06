from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.clients import BaseProviderClient, EventsProviderClient
from app.core import get_session, settings
from app.repository import (
    BaseRepository,
    get_event_repository,
    get_place_repository,
    get_sync_repository,
)
from app.services import SyncService
from app.utils import EventsPaginator


async def get_events_provider_client():
    return EventsProviderClient(
        base_url=settings.provider_base_url,
        api_key=settings.provider_api_key
    )


async def get_events_paginator_class():
    return EventsPaginator


SessionDep = Annotated[AsyncSession, Depends(get_session)]

EventsRepoDep = Annotated[BaseRepository, Depends(get_event_repository)]
PlaceRepoDep = Annotated[BaseRepository, Depends(get_place_repository)]
SyncRepoDep = Annotated[BaseRepository, Depends(get_sync_repository)]

EventsProviderClientDep = Annotated[
    BaseProviderClient,
    Depends(get_events_provider_client)
]
EventsPaginatorClassDep = Annotated[
    type[EventsPaginator],
    Depends(get_events_paginator_class)
]


async def get_sync_service(
        client: EventsProviderClientDep,
        paginator_class: EventsPaginatorClassDep,
        sync_repo: SyncRepoDep,
        events_repo: EventsRepoDep,
        place_repo: PlaceRepoDep
):
    return SyncService(
        client=client,
        paginator_class=paginator_class,
        sync_repo=sync_repo,
        events_repo=events_repo,
        place_repo=place_repo
    )


SyncServiceDep = Annotated[SyncService, Depends(get_sync_service)]
