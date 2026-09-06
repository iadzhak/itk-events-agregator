from app.models import SyncMeta
from app.repository.base import BaseRepository

sync_repository = BaseRepository(SyncMeta)


async def get_sync_repository():
    return sync_repository
