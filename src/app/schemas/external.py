from pydantic import AnyHttpUrl, BaseModel, EmailStr

from app.schemas.event import Event


class EventsResponse(BaseModel):
    next: AnyHttpUrl | None
    previous: AnyHttpUrl | None
    results: list[Event]


class RegisterForm(BaseModel):
    first_name: str
    last_name: str
    seat: str
    email: EmailStr
