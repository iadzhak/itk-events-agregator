from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .event import Event

from uuid import UUID

from sqlalchemy import UUID as UUID_sa
from sqlalchemy import Boolean, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core import Base


class Ticket(Base):
    __table_args__ = (
        UniqueConstraint('ticket_id', 'event_id', name='uq_event_tickets'),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ticket_id: Mapped[UUID] = mapped_column(UUID_sa)
    event_id: Mapped[UUID] = mapped_column(ForeignKey('event.id'))
    sold: Mapped[bool] = mapped_column(Boolean)
    first_name: Mapped[str | None] = mapped_column(String, nullable=True)
    last_name: Mapped[str | None] = mapped_column(String, nullable=True)
    email: Mapped[str | None] = mapped_column(String, nullable=True)

    event: Mapped['Event'] = mapped_column(back_populates='tickets')
