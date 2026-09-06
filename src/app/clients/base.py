import datetime as dt
from abc import ABC, abstractmethod
from uuid import UUID

from app.schemas import EventsExternal


class BaseProviderClient(ABC):

    @abstractmethod
    async def events(
            self,
            changed_at: dt.datetime,
            cursor: str | None = None
    ) -> EventsExternal:
        pass

    @abstractmethod
    async def seats(self, event_id: UUID) -> list[str]:
        pass

    @abstractmethod
    async def register(
            self,
            event_id: UUID,
            first_name: str,
            last_name: str,
            seat: str,
            email: str
    ) -> UUID:
        pass

    @abstractmethod
    async def cancel(self, event_id: UUID, ticket_id: UUID) -> bool:
        pass
