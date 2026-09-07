from app.models import Ticket
from app.repository.base import BaseRepository


class TicketRepository(BaseRepository):
    model = Ticket

    async def create(self, data: dict) -> Ticket:
        ticket = Ticket(**data)
        self.session.add(ticket)
        await self.session.commit()
        return ticket
