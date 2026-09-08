import datetime as dt
from uuid import uuid4

import pytest

from app.schemas import EventDB, PlaceDB


def generate_date(days_delta: int = 0):
    return dt.datetime.now(tz=dt.UTC) + dt.timedelta(days=days_delta)


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
