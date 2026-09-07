import datetime as dt
from uuid import UUID

from app.clients import EventsProviderClient
from app.core import BadRequestError, ExternalApiError, NotFoundError
from app.repository import TicketRepository
from app.schemas import CancelTicket


class CancelTicketUseCase:
    def __init__(
            self,
            client: EventsProviderClient,
            tickets: TicketRepository
    ):
        self._client = client
        self._tickets = tickets

    async def do(self, ticket_id: UUID) -> CancelTicket:
        # check registration exist
        ticket = await self._tickets.get_by_id(ticket_id)
        if ticket is None:
            raise NotFoundError(
                f'Билет "{ticket_id}" не найден'
            )

        # check event has not passed
        now = dt.datetime.now(tz=dt.UTC)
        if now >= ticket.event.event_time:
            raise BadRequestError(
                f'Мероприятие "{ticket.event.name}" уже прошло'
            )
        # check response
        response = await self._client.cancel(ticket.event.id, ticket_id)
        if not response:
            raise ExternalApiError('Не удалось отменить регистрацию')

        await self._tickets.delete(ticket)
        return CancelTicket()
