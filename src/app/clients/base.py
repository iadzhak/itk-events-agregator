import datetime as dt
from typing import Protocol
from uuid import UUID

from app.schemas import EventsExternal


class BaseProviderClient(Protocol):
    async def events(
        self, changed_at: dt.datetime, cursor: str | None = None
    ) -> EventsExternal:
        pass

    async def seats(self, event_id: UUID) -> list[str]:
        pass

    async def register(
        self,
        event_id: UUID,
        first_name: str,
        last_name: str,
        seat: str,
        email: str,
    ) -> UUID:
        pass

    async def cancel(self, event_id: UUID, ticket_id: UUID) -> bool:
        pass
