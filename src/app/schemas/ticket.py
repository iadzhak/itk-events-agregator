from uuid import UUID

from pydantic import BaseModel


class Ticket(BaseModel):
    ticket_id: UUID
