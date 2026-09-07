from typing import Annotated

from cachetools import TTLCache
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.clients import EventsProviderClient
from app.core import get_session, settings
from app.flows import CancelTicketUseCase, CreateTicketUseCase
from app.repository import (
    EventRepository,
    PlaceRepository,
    SyncRepository,
    TicketRepository,
)
from app.services import EventService, SyncService, get_seats_cache
from app.utils import EventsPaginator, get_events_paginator_class


async def get_events_provider_client():
    client = EventsProviderClient(
        base_url=settings.provider_base_url,
        api_key=settings.provider_api_key,
        retries=settings.provider_retries,
    )
    yield client
    await client.aclose()


SessionDep = Annotated[AsyncSession, Depends(get_session)]


def get_event_repository(session: SessionDep) -> EventRepository:
    return EventRepository(session)


def get_place_repository(session: SessionDep) -> PlaceRepository:
    return PlaceRepository(session)


def get_sync_repository(session: SessionDep) -> SyncRepository:
    return SyncRepository(session)


def get_ticket_repository(session: SessionDep) -> TicketRepository:
    return TicketRepository(session)


EventsRepoDep = Annotated[EventRepository, Depends(get_event_repository)]
PlaceRepoDep = Annotated[PlaceRepository, Depends(get_place_repository)]
SyncRepoDep = Annotated[SyncRepository, Depends(get_sync_repository)]
TicketRepoDep = Annotated[TicketRepository, Depends(get_ticket_repository)]

EventsProviderClientDep = Annotated[
    EventsProviderClient, Depends(get_events_provider_client)
]
EventsPaginatorClassDep = Annotated[
    type[EventsPaginator], Depends(get_events_paginator_class)
]


def get_sync_service(
    client: EventsProviderClientDep,
    paginator_class: EventsPaginatorClassDep,
    sync_repo: SyncRepoDep,
    events_repo: EventsRepoDep,
    place_repo: PlaceRepoDep,
):
    return SyncService(
        client=client,
        paginator_class=paginator_class,
        sync_repo=sync_repo,
        events_repo=events_repo,
        place_repo=place_repo,
    )


SyncServiceDep = Annotated[SyncService, Depends(get_sync_service)]

SeatsCacheDep = Annotated[TTLCache, Depends(get_seats_cache)]


def get_events_service(
    client: EventsProviderClientDep, repo: EventsRepoDep, cache: SeatsCacheDep
):
    return EventService(client=client, repo=repo, cache=cache)


EventServiceDep = Annotated[EventService, Depends(get_events_service)]


def get_create_ticket_use_case(
    client: EventsProviderClientDep,
    events: EventsRepoDep,
    tickets: TicketRepoDep,
) -> CreateTicketUseCase:
    return CreateTicketUseCase(client, events, tickets)


CreateTicketUseCaseDep = Annotated[
    CreateTicketUseCase, Depends(get_create_ticket_use_case)
]


def get_cancel_ticket_use_case(
    client: EventsProviderClientDep, tickets: TicketRepoDep
) -> CancelTicketUseCase:
    return CancelTicketUseCase(client, tickets)


CancelTicketUseCaseDep = Annotated[
    CancelTicketUseCase, Depends(get_cancel_ticket_use_case)
]
