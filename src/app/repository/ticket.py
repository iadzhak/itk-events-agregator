from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from app.models import Ticket
from app.repository.base import BaseRepository
from app.types import TicketStatus


class TicketRepository(BaseRepository):
    model = Ticket

    async def create(self, data: dict) -> Ticket:
        ticket = Ticket(**data)
        self.session.add(ticket)
        try:
            await self.session.flush()
        except IntegrityError as e:
            await self.session.rollback()
            ticket_in_db = await self.get_by_id(ticket.id)
            if ticket_in_db and ticket_in_db.status == TicketStatus.CANCELLED:
                data['status'] = TicketStatus.BOUGHT
                return await self.update(ticket_in_db, data)
            raise RuntimeError(
                f'Не удалось создать в базе запись для билета {ticket.id}'
            ) from e
        return ticket

    async def count_cancelled(self) -> int:
        stmt = select(func.count(Ticket.id)).where(
            Ticket.status == TicketStatus.CANCELLED
        )
        result = await self.session.execute(stmt)
        return int(result.scalars().first() or 0)

    async def delete(self, db_obj: Ticket) -> Ticket:
        db_obj.status = TicketStatus.CANCELLED
        await self.session.flush()
        return db_obj
