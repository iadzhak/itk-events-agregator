from sqlalchemy import select

from app.models import Outbox
from app.repository.base import BaseRepository
from app.types import OutboxStatus


class OutboxRepository(BaseRepository):
    model = Outbox

    async def get_for_processing(self, max_retries: int) -> list[Outbox]:
        stmt = (
            select(Outbox)
            .where(
                (Outbox.status == OutboxStatus.PENDING)
                | (
                    (Outbox.status == OutboxStatus.FAILED)
                    & (Outbox.retry_count <= max_retries)
                )
            )
            .order_by(Outbox.last_changed_at)
            .with_for_update(skip_locked=True)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
