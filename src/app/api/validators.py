import datetime as dt
import re
from typing import cast
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Event
from app.repository import EventRepository
from app.types import EventStatus


async def is_event_exist(
        event_id: UUID,
        repo: EventRepository,
        session: AsyncSession
) -> Event:
    event = await repo.get_by_id(event_id, session)
    if event is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Мероприятие не найдено'
        )
    return cast(Event, event)


def is_event_published(event: Event):
    if event.status != EventStatus.PUBLISHED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Мероприятие не опубликовано'
        )


def is_event_deadline(event: Event):
    now = dt.datetime.now(tz=dt.UTC)
    if now >= event.registration_deadline:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Регистрация на мероприятие закрыта'
        )


def is_seat_exist(seat: str, seat_pattern: str):
    range_pattern = re.compile(r'([A-Z])(\d+)-(\d+)')
    place_pattern = re.compile(r'([A-Z])(\d+)')
    parts = seat_pattern.split(',')
    available = {}
    for part in parts:
        m = range_pattern.match(part)
        section, min_place, max_place = m.groups()
        available[section] = int(min_place), int(max_place)
    s, p = place_pattern.match(seat).groups()
    p = int(p)
    if s not in available:
        all_s = ','.join(available.keys())
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Секции {s} нет среди доступных: {all_s}'
        )
    if p < available[s][0] or p > available[s][1]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Места {p} нет среди возможных '
                   f'{available[s][0]}-{available[s][1]} в секции {s}'
        )
