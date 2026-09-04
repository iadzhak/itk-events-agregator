import datetime as dt
from uuid import UUID

from pydantic import BaseModel


class CommonMixin(BaseModel):
    id: UUID
    name: str
    changed_at: dt.datetime
    created_at: dt.datetime
