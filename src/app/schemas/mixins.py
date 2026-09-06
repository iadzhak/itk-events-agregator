import datetime as dt
from uuid import UUID

from pydantic import BaseModel


class BaseEntityMixin(BaseModel):
    id: UUID
    name: str


class DateTrackMixin(BaseModel):
    changed_at: dt.datetime
    created_at: dt.datetime


class CommonMixin(BaseEntityMixin, DateTrackMixin):
    pass
