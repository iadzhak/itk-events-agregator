from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .event import Event

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core import BaseUUID, CommonMixin


class Place(CommonMixin, BaseUUID):
    city: Mapped[str] = mapped_column(String)
    address: Mapped[str] = mapped_column(String)
    seats_pattern: Mapped[str] = mapped_column(String)

    events: Mapped[list['Event']] = relationship(back_populates='place')
