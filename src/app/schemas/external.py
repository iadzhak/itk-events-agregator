from pydantic import AnyHttpUrl, BaseModel, EmailStr

from app.schemas.event import EventDB


class EventsResponse(BaseModel):
    next: AnyHttpUrl | None
    previous: AnyHttpUrl | None
    results: list[EventDB]


class RegisterForm(BaseModel):
    first_name: str
    last_name: str
    seat: str
    email: EmailStr
