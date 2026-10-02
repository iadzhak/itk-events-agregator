from sqlalchemy import func, select

from app.models import Ticket
from app.repository.base import BaseRepository
from app.types import TicketStatus


class TicketRepository(BaseRepository):
    model = Ticket

    async def create(self, data: dict) -> Ticket:
        ticket = Ticket(**data)
        self.session.add(ticket)
        await self.session.flush()
        return ticket

    async def count_by_status(self, status: TicketStatus) -> int:
        stmt = select(func.count(Ticket.id)).where(Ticket.status == status)
        result = await self.session.execute(stmt)
        return int(result.scalars().first() or 0)
