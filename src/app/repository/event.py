from app.models.event import Event
from app.repository.base import BaseRepository

event_repository = BaseRepository(Event)


async def get_event_repository():
    return event_repository
