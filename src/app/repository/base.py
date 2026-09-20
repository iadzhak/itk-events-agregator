from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import BaseInt, BaseUUID


class BaseRepository[T: BaseInt | BaseUUID]:
    model: type[T]

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, data: dict) -> T:
        new_obj = self.model(**data)
        self.session.add(new_obj)
        try:
            await self.session.commit()
            return new_obj
        except IntegrityError as e:
            await self.session.rollback()
            db_obj = await self.get_by_id(data['id'])
            if db_obj is None:
                raise RuntimeError(
                    f'{self.model.__name__} object with id {data["id"]} '
                    f'not found after IntegrityError'
                ) from e
        return db_obj

    async def get_by_id(
        self,
        _id: int | UUID,
    ) -> T | None:
        stmt = select(self.model).where(self.model.id == _id)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def update(self, db_obj: T, data: dict) -> T:
        columns = self.model.__mapper__.columns.keys()
        for key in columns:
            if key in data:
                setattr(db_obj, key, data[key])
        self.session.add(db_obj)
        await self.session.commit()
        return db_obj

    async def delete(self, db_obj: T) -> T:
        await self.session.delete(db_obj)
        await self.session.commit()
        return db_obj
