from app.models.place import Place
from app.repository.base import BaseRepository

place_repository = BaseRepository(Place)


async def get_place_repository():
    return place_repository
