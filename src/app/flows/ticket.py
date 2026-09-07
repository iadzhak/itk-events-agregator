from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.clients import BaseProviderClient
from app.core.exceptions import EventNotFound, EventUnexpectedStatus
from app.repository import EventRepository
from app.types import EventStatus


class CreateTicketUseCase:
    def __init__(self, client: BaseProviderClient, events: EventRepository):
        self._client = client
        self._events = events

    async def do(self, event_id: UUID, first_name: str, seat: str,
                 session: AsyncSession):
        event = await self._events.get_by_id(event_id, session)
        if event is None:
            raise EventNotFound(f'Мероприятие с id: {event_id!s} '
                                f'не найдено')
        if event.status != EventStatus.PUBLISHED:
            raise EventUnexpectedStatus(
                f'Мероприятие "{event.name}" не опубликовано, '
                f'текущий статус: "{event.status}"')
