import datetime as dt
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class PlaceBase(BaseModel):
    id: UUID
    name: str


class PlaceOut(PlaceBase):
    city: str
    address: str
    seats_pattern: str

    model_config = ConfigDict(from_attributes=True)


class PlaceDB(PlaceOut):
    changed_at: dt.datetime
    created_at: dt.datetime
