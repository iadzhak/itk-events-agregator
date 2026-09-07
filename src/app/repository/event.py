from typing import cast
from uuid import UUID

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models import Event
from app.repository.base import BaseRepository
from app.schemas import EventFilter


class EventRepository(BaseRepository):

    def _apply_filters(self, stmt: Select, filters: EventFilter) -> Select:
        if filters.date_from is not None:
            stmt = stmt.where(Event.event_time >= filters.date_from)
        return stmt

    def _select_joined(self) -> Select:
        return select(Event).options(joinedload(Event.place))

    async def get_paginated(
            self,
            filters: EventFilter,
            limit: int,
            offset: int,
            session: AsyncSession
    ) -> tuple[list[Event], int]:
        stmt = self._select_joined()
        stmt = self._apply_filters(stmt, filters)
        stmt = stmt.order_by(Event.event_time).limit(limit).offset(offset)

        count_stmt = select(func.count()).select_from(Event)
        count_stmt = self._apply_filters(count_stmt, filters)

        result_items = await session.execute(stmt)
        items = cast(list[Event], result_items.scalars().all())

        result_count = await session.execute(count_stmt)
        count = cast(int, result_count.scalar_one())
        return items, count

    async def get_detail(
            self,
            _id: UUID,
            session: AsyncSession
    ) -> Event | None:
        stmt = self._select_joined().where(Event.id == _id)
        result = await session.execute(stmt)
        return result.scalars().first()


event_repository = EventRepository(Event)


async def get_event_repository():
    return event_repository
