import datetime as dt

from pydantic import BaseModel

from app.schemas.mixins import CommonMixin
from app.schemas.place import PlaceDB
from app.types.event_status import EventStatus


class EventDB(CommonMixin, BaseModel):
    place: PlaceDB
    event_time: dt.datetime
    registration_deadline: dt.datetime
    status: EventStatus | str
    number_of_visitors: int
    status_changed_at: dt.datetime
