from app.models import SyncMeta
from app.repository.base import BaseRepository


class SyncRepository(BaseRepository):
    model = SyncMeta
