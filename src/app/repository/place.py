from app.repository.base import BaseRepository
from app.models.place import Place

place_repository = BaseRepository(Place)


async def get_place_repository():
    return place_repository
