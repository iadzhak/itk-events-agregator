from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.repository import EventRepository
from app.types import EventStatus


async def is_event_published(
        event_id: UUID,
        repo: EventRepository,
        session: AsyncSession
):
    event = await repo.get_by_id(event_id, session)
    if event is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Мероприятие не найдено'
        )
    if event.status != EventStatus.PUBLISHED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Мероприятие не опубликовано'
        )
