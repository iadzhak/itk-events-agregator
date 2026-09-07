from uuid import UUID

from sqlalchemy import select

from app.models import Ticket
from app.repository.base import BaseRepository


class TicketRepository(BaseRepository):
    model = Ticket

    async def get_by_ticket_id(self, ticket_id: UUID) -> Ticket | None:
        stmt = select(Ticket).where(Ticket.ticket_id == ticket_id)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def create(self, data: dict) -> Ticket:
        ticket = Ticket(**data)
        self.session.add(ticket)
        await self.session.commit()
        return ticket
