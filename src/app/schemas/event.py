import datetime as dt
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

from app.schemas.place import PlaceDB, PlaceOut, PlaceFull
from app.types import EventStatus


class EventBase(BaseModel):
    id: UUID
    name: str


class EventOut(EventBase):
    place: PlaceOut
    event_time: dt.datetime
    registration_deadline: dt.datetime
    status: EventStatus | str
    number_of_visitors: int

    model_config = ConfigDict(from_attributes=True)


class EventDetail(EventOut):
    place: PlaceFull


class EventDB(EventOut):
    place: PlaceDB
    status_changed_at: dt.datetime
    changed_at: dt.datetime
    created_at: dt.datetime


class EventsExternal(BaseModel):
    next: HttpUrl | None
    previous: HttpUrl | None
    results: list[EventDB]


class EventFilter(BaseModel):
    date_from: dt.date | None = Field(
        None, description='События после этой даты (YYYY-MM-DD)'
    )


class EventSeatsResponse(BaseModel):
    event_id: UUID
    available_seats: list[str] = Field(examples=[['A1', 'A3', 'A4']])
