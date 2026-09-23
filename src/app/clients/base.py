import datetime as dt
from typing import Protocol
from uuid import UUID

from app.schemas import EventsExternal


class BaseProviderClient(Protocol):
    async def events(
        self, changed_at: dt.datetime, cursor: str | None = None
    ) -> EventsExternal: ...

    async def seats(self, event_id: UUID) -> list[str]: ...

    async def register(
        self,
        event_id: UUID,
        first_name: str,
        last_name: str,
        seat: str,
        email: str,
    ) -> UUID: ...

    async def cancel(self, event_id: UUID, ticket_id: UUID) -> bool: ...


class BaseNotificationClient(Protocol):
    async def notify(
        self,
        msg: str,
        reference_id: str | UUID,
        idempotency_key: str | UUID | None = None,
    ) -> None: ...
