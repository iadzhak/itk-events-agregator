from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .event import Event

from uuid import UUID

from sqlalchemy import UUID as UUID_SA
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core import Base


class Ticket(Base):
    id: Mapped[UUID] = mapped_column(UUID_SA, primary_key=True)
    seat: Mapped[str] = mapped_column(String, nullable=False)
    event_id: Mapped[UUID] = mapped_column(ForeignKey('event.id'))
    first_name: Mapped[str] = mapped_column(String)
    last_name: Mapped[str] = mapped_column(String)
    email: Mapped[str] = mapped_column(String)

    event: Mapped['Event'] = relationship(
        back_populates='tickets', lazy='selectin'
    )
