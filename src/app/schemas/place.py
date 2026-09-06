import datetime as dt
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class PlaceBase(BaseModel):
    id: UUID
    name: str


class PlaceOut(PlaceBase):
    city: str
    address: str


class PlaceDB(PlaceOut):
    seats_pattern: str
    changed_at: dt.datetime
    created_at: dt.datetime

    model_config = ConfigDict(from_attributes=True)
