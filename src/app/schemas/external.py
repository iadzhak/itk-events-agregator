from pydantic import AnyHttpUrl, BaseModel

from app.schemas.event import EventDB


class EventsResponse(BaseModel):
    next: AnyHttpUrl | None
    previous: AnyHttpUrl | None
    results: list[EventDB]
