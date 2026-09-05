from pydantic import BaseModel

from app.schemas.mixins import CommonMixin


class PlaceDB(CommonMixin, BaseModel):
    city: str
    address: str
    seats_pattern: str
