from app.models import Place
from app.repository.base import BaseRepository


class PlaceRepository(BaseRepository):
    model = Place
