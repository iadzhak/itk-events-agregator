from typing import Annotated

from fastapi import APIRouter, Depends, Request

from app.dependencies import EventServiceDep, SessionDep
from app.schemas import EventFilter, Pagination

router = APIRouter()


@router.get('/')
async def get_all_events(
        *,
        filters: Annotated[EventFilter, Depends()],
        pagination: Annotated[Pagination, Depends()],
        event_service: EventServiceDep,
        session: SessionDep,
        request: Request,
):
    result = await event_service.get_paginated(request, filters, pagination,
                                               session)
    return result


@router.get('/{event_id}')
async def get_event_details(event_id):
    return None


@router.get('/{event_id}/seats')
async def get_available_seats(event_id):
    return None
