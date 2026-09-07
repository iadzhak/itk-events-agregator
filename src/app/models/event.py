from typing import TYPE_CHECKING
from uuid import UUID

if TYPE_CHECKING:
    from .place import Place
    from .ticket import Ticket

import datetime as dt

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core import Base, CommonMixin


class Event(CommonMixin, Base):
    event_time: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True))
    registration_deadline: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True)
    )
    status: Mapped[str] = mapped_column(String)
    number_of_visitors: Mapped[int] = mapped_column(Integer)
    status_changed_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True)
    )
    place_id: Mapped[UUID] = mapped_column(ForeignKey('place.id'))

    place: Mapped['Place'] = relationship(
        back_populates='events', lazy='selectin'
    )
    tickets: Mapped[list['Ticket']] = relationship(
        back_populates='event', lazy='selectin'
    )
