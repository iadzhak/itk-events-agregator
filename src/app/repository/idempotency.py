from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

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

    async def create(self, data) -> Idempotency:
        new_obj = self.model(**data)
        self.session.add(new_obj)
        try:
            await self.session.flush()
        except IntegrityError:
            await self.session.rollback()
            raise
        return new_obj
