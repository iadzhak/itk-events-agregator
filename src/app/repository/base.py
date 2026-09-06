from uuid import UUID

from fastapi.encoders import jsonable_encoder
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession


class BaseRepository[T]:
    def __init__(self, model: type[T]):
        self.model = model

    async def create(self, data: dict, session: AsyncSession) -> T:
        db_obj = self.model(**data)
        session.add(db_obj)
        try:
            await session.commit()
        except IntegrityError:
            db_obj = await self.get_by_id(data['id'], session)
        return db_obj

    async def get_by_id(
            self,
            _id: int | UUID,
            session: AsyncSession
    ) -> T | None:
        stmt = select(self.model).where(self.model.id == _id)
        result = await session.execute(stmt)
        return result.scalars().first()

    async def update(self, db_obj: T, data: dict, session: AsyncSession) -> T:
        db_obj_data = jsonable_encoder(db_obj)
        for key in db_obj_data:
            if key in data:
                setattr(db_obj, key, data[key])
        session.add(db_obj)
        await session.commit()
        return db_obj
