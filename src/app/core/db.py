import datetime as dt
from uuid import UUID

from sqlalchemy import UUID as UUID_sa
from sqlalchemy import DateTime, String
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    declared_attr,
    mapped_column,
)

from app.core.conf import settings

engine = create_async_engine(settings.db_url)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    @declared_attr
    def __tablename__(cls) -> str:
        return cls.__name__.lower()


class CommonMixin:
    id: Mapped[UUID] = mapped_column(UUID_sa, primary_key=True)
    name: Mapped[str] = mapped_column(String)
    changed_at: Mapped[dt.datetime] = mapped_column(DateTime)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime)


async def get_session():
    async with AsyncSessionLocal() as session:
        yield session
