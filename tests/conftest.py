import datetime as dt
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.schemas.event import EventDB
from app.schemas.place import PlaceDB


def generate_date(days_delta: int = 0):
    return dt.datetime.now(tz=dt.UTC) + dt.timedelta(days=days_delta)


@pytest_asyncio.fixture(scope='session')
async def test_client():
    async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url='http://test'
    ) as client:
        yield client


@pytest.fixture
def place_factory():
    def func(name: str = 'place'):
        return PlaceDB(
            id=uuid4(),
            name=name,
            city='city',
            address='address',
            seats_pattern="A1-1000,B1-2000",
            changed_at=generate_date(-1),
            created_at=generate_date(-10),
        )

    return func


@pytest.fixture
def event_factory(place_factory):
    def func(name: str = 'event', place: PlaceDB | None = None):
        return EventDB(
            id=uuid4(),
            name=name,
            place=place or place_factory(),
            event_time=generate_date(5),
            registration_deadline=generate_date(1),
            status='published',
            number_of_visitors=5,
            changed_at=generate_date(-1),
            created_at=generate_date(-10),
            status_changed_at=generate_date(-1)
        )

    return func
