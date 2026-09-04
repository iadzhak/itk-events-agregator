import datetime as dt

from pydantic import BaseModel

from app.schemas.mixins import CommonMixin
from app.schemas.place import Place
from app.types.status import Status


class Event(CommonMixin, BaseModel):
    place: Place
    event_time: dt.datetime
    registration_deadline: dt.datetime
    status: Status | str
    number_of_visitors: int
    status_changed_at: dt.datetime
