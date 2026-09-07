from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class User(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr


class UserBuyTicket(User):
    event_id: UUID
    seat: str = Field(..., pattern=r'^[A-Z][1-9]\d*$', examples=['A17'])


class Ticket(BaseModel):
    ticket_id: UUID


class CancelTicket(BaseModel):
    success: bool = True
