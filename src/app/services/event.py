from uuid import UUID

from fastapi import Request
from pydantic import HttpUrl
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import EventNotFound
from app.repository import EventRepository
from app.schemas import EventFilter, EventOut, PaginatedResponse, Pagination


class EventService:
    def __init__(self, repo: EventRepository):
        self.repo = repo

    async def get(
            self,
            event_id: UUID,
            session: AsyncSession
    ) -> EventOut:
        event = await self.repo.get_by_id(event_id, session)
        if event is None:
            raise EventNotFound(f'Мероприятие id "{str(event_id)}" не найдено')
        return EventOut.model_validate(event)

    async def get_paginated(
            self,
            filters: EventFilter,
            pagination: Pagination,
            request: Request,
            session: AsyncSession,
    ) -> PaginatedResponse[EventOut]:
        limit = pagination.page_size
        offset = (pagination.page - 1) * limit
        items, total = await self.repo.get_paginated(
            filters=filters,
            limit=limit,
            offset=offset,
            session=session
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
