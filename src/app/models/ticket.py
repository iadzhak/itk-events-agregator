from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .event import Event

from uuid import UUID

from sqlalchemy import UUID as UUID_sa
from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core import Base


class Ticket(Base):
    __table_args__ = (
        UniqueConstraint('ticket_id', 'event_id', name='uq_event_tickets'),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ticket_id: Mapped[UUID] = mapped_column(UUID_sa, nullable=False)
    seat: Mapped[str] = mapped_column(String, nullable=False)
    event_id: Mapped[UUID] = mapped_column(ForeignKey('event.id'))
    first_name: Mapped[str] = mapped_column(String)
    last_name: Mapped[str] = mapped_column(String)
    email: Mapped[str] = mapped_column(String)

    event: Mapped['Event'] = relationship(
        back_populates='tickets',
        lazy='selectin'
    )
