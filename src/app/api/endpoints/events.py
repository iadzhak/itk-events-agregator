from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Request

from app.dependencies import (
    EventServiceDep,
)
from app.schemas import (
    EventFilter,
    EventOut,
    EventSeatsResponse,
    PaginatedResponse,
    Pagination,
)

router = APIRouter()


@router.get('', response_model=PaginatedResponse[EventOut])
async def get_all_events(
    filters: Annotated[EventFilter, Depends()],
    pagination: Annotated[Pagination, Depends()],
    event_service: EventServiceDep,
    request: Request,
):
    return await event_service.get_paginated(
        request=request,
        filters=filters,
        pagination=pagination,
    )


@router.get('/{event_id}', response_model=EventOut)
async def get_event_details(
    event_id: UUID,
    event_service: EventServiceDep,
):
    return await event_service.get(event_id)


@router.get('/{event_id}/seats', response_model=EventSeatsResponse)
async def get_available_seats(
    event_id: UUID,
    event_service: EventServiceDep,
):
    return await event_service.get_available_seats_cached(event_id)
