from sqlalchemy import select

from app.models import Idempotency
from app.repository.base import BaseRepository


class IdempotencyRepository(BaseRepository):
    model = Idempotency

    async def update(self, db_obj: Idempotency, data: dict) -> Idempotency:
        raise TypeError('Для данного репозитория не предусмотрено обновление')

    async def get_by_key(self, idempotency_key: str) -> Idempotency | None:
        stmt = select(Idempotency).where(
            Idempotency.idempotency_key == idempotency_key
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()
