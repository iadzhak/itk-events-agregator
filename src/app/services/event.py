from uuid import UUID

from cachetools import TTLCache
from fastapi import Request
from pydantic import HttpUrl

from app.clients import BaseProviderClient
from app.core import BadRequest, NotFound
from app.repository import EventRepository
from app.schemas import (
    EventFilter,
    EventOut,
    EventSeatsResponse,
    PaginatedResponse,
    Pagination,
)
from app.types import EventStatus

CACHE_MAX_SIZE = 30
CACHE_TTL = 30

seats_cache = TTLCache(maxsize=CACHE_MAX_SIZE, ttl=CACHE_TTL)


def get_seats_cache():
    return seats_cache


class EventService:
    def __init__(
            self,
            client: BaseProviderClient,
            repo: EventRepository,
            cache: TTLCache
    ):
        self._client = client
        self._repo = repo
        self._cache = cache

    async def get(self, event_id: UUID) -> EventOut:
        event = await self._repo.get_by_id(event_id)
        if event is None:
            raise NotFound(f'Мероприятие id "{event_id!s}" не найдено')
        return EventOut.model_validate(event)

    async def get_paginated(
            self,
            filters: EventFilter,
            pagination: Pagination,
            request: Request,
    ) -> PaginatedResponse[EventOut]:
        limit = pagination.page_size
        offset = (pagination.page - 1) * limit
        items, total = await self._repo.get_paginated(
            filters=filters,
            limit=limit,
            offset=offset
        )

        next_url = None
        previous_url = None
        if limit + offset < total:
            next_url = str(
                request.url.include_query_params(page=pagination.page + 1)
            )
        if pagination.page > 1:
            previous_url = str(
                request.url.include_query_params(page=pagination.page - 1)
            )

        return PaginatedResponse(
            count=total,
            next=HttpUrl(next_url) if next_url else None,
            previous=HttpUrl(previous_url) if previous_url else None,
            results=[EventOut.model_validate(i) for i in items]
        )

    async def get_available_seats(self, event_id: UUID) -> list[str]:
        event = await self.get(event_id)
        if event.status != EventStatus.PUBLISHED:
            raise BadRequest(
                f'Получить информацию о местах можно только у мероприятий со '
                f'статусом "published". У мероприятия "{event.name}" '
                f'статус "{event.status}"'
            )

        seats = await self._client.seats(event.id)
        self._cache[event_id] = tuple(seats)
        return seats

    async def get_available_seats_cached(
            self,
            event_id: UUID
    ) -> EventSeatsResponse:
        if event_id not in self._cache:
            await self.get_available_seats(event_id)
        seats = self._cache[event_id]
        return EventSeatsResponse(
            event_id=event_id,
            available_seats=list(seats)
        )
