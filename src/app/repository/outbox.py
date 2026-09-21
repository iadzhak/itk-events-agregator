from app.models import Outbox
from app.repository.base import BaseRepository


class OutboxRepository(BaseRepository):
    model = Outbox
