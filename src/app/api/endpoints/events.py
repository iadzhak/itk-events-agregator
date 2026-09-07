from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Request

from app.api.validators import is_event_published
from app.dependencies import (
    AvailableSeatsUseCaseDep,
    EventServiceDep,
    EventsRepoDep,
    SessionDep,
)
from app.schemas import (
    EventFilter,
    EventOut,
    EventSeatsResponse,
    PaginatedResponse,
    Pagination,
)

router = APIRouter()


@router.get('/', response_model=PaginatedResponse[EventOut])
async def get_all_events(
        *,
        filters: Annotated[EventFilter, Depends()],
        pagination: Annotated[Pagination, Depends()],
        event_service: EventServiceDep,
        session: SessionDep,
        request: Request
):
    return await event_service.get_paginated(
        request=request,
        filters=filters,
        pagination=pagination,
        session=session
    )


@router.get('/{event_id}', response_model=EventOut)
async def get_event_details(
        event_id: UUID,
        event_repo: EventsRepoDep,
        session: SessionDep
):
    return await event_repo.get_detail(event_id, session)


@router.get('/{event_id}/seats', response_model=EventSeatsResponse)
async def get_available_seats(
        event_id: UUID,
        repo: EventsRepoDep,
        session: SessionDep,
        available_seats_use_case: AvailableSeatsUseCaseDep
):
    await is_event_published(event_id, repo, session)
    return await available_seats_use_case.do(event_id)
