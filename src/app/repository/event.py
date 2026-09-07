from typing import cast
from uuid import UUID

from sqlalchemy import Select, func, select

from app.models import Event
from app.repository.base import BaseRepository
from app.schemas import EventFilter


class EventRepository(BaseRepository):
    model = Event

    def _apply_filters(self, stmt: Select, filters: EventFilter) -> Select:
        if filters.date_from is not None:
            stmt = stmt.where(Event.event_time >= filters.date_from)
        return stmt

    async def get_paginated(
            self,
            filters: EventFilter,
            limit: int,
            offset: int) -> tuple[list[Event], int]:
        stmt = select(Event)
        stmt = self._apply_filters(stmt, filters)
        stmt = stmt.order_by(Event.event_time).limit(limit).offset(offset)

        count_stmt = select(func.count()).select_from(Event)
        count_stmt = self._apply_filters(count_stmt, filters)

        result_items = await self.session.execute(stmt)
        items = cast(list[Event], result_items.scalars().all())

        result_count = await self.session.execute(count_stmt)
        count = cast(int, result_count.scalar_one())
        return items, count

    async def get_detail(self, _id: UUID, ) -> Event | None:
        stmt = select(Event).where(Event.id == _id)
        result = await self.session.execute(stmt)
        return result.scalars().first()
