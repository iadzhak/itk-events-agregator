from typing import TypeAlias
from urllib.parse import parse_qs, urlencode, urlparse
from uuid import UUID

from cachetools import TTLCache
from pydantic import HttpUrl

from app.clients import BaseProviderClient
from app.core import BadRequestError, NotFoundError
from app.repository import EventRepository
from app.schemas import (
    EventDetail,
    EventFilter,
    EventOut,
    EventSeatsResponse,
    PaginatedResponse,
    Pagination,
)
from app.types import EventStatus

CACHE_MAX_SIZE = 30
CACHE_TTL = 30

SCT: TypeAlias = TTLCache[UUID, list[str]]

seats_cache: SCT = TTLCache(maxsize=CACHE_MAX_SIZE, ttl=CACHE_TTL)


def get_seats_cache() -> SCT:
    return seats_cache


class EventService:
    def __init__(
        self,
        client: BaseProviderClient,
        repo: EventRepository,
        cache: TTLCache,
    ):
        self._client = client
        self._repo = repo
        self._cache = cache

    async def get(self, event_id: UUID) -> EventDetail:
        event = await self._repo.get_by_id(event_id)
        if event is None:
            raise NotFoundError(f'Мероприятие id "{event_id!s}" не найдено')
        return EventDetail.model_validate(event)

    async def get_paginated(
        self, filters: EventFilter, pagination: Pagination, current_url: str
    ) -> PaginatedResponse[EventOut]:
        limit = pagination.page_size
        offset = (pagination.page - 1) * limit
        items, total = await self._repo.get_paginated(
            filters=filters, limit=limit, offset=offset
        )

        next_url = None
        previous_url = None
        parsed_url = urlparse(current_url)
        if limit + offset < total:
            query = parse_qs(parsed_url.query)
            query['page'] = [str(pagination.page + 1)]
            query_str = urlencode(query, doseq=True)
            next_url = parsed_url._replace(query=query_str).geturl()
        if pagination.page > 1:
            query = parse_qs(parsed_url.query)
            query['page'] = [str(pagination.page - 1)]
            query_str = urlencode(query, doseq=True)
            previous_url = parsed_url._replace(query=query_str).geturl()

        return PaginatedResponse(
            count=total,
            next=HttpUrl(next_url) if next_url else None,
            previous=HttpUrl(previous_url) if previous_url else None,
            results=[EventOut.model_validate(i) for i in items],
        )

    async def get_available_seats(self, event_id: UUID) -> list[str]:
        event = await self.get(event_id)
        if event.status != EventStatus.PUBLISHED:
            raise BadRequestError(
                f'Получить информацию о местах можно только у мероприятий со '
                f'статусом "published". У мероприятия "{event.name}" '
                f'статус "{event.status}"'
            )

        seats = await self._client.seats(event.id)
        self._cache[event_id] = tuple(seats)
        return seats

    async def get_available_seats_cached(
        self, event_id: UUID
    ) -> EventSeatsResponse:
        if event_id not in self._cache:
            await self.get_available_seats(event_id)
        seats = self._cache[event_id]
        return EventSeatsResponse(
            event_id=event_id, available_seats=list(seats)
        )
