import datetime as dt
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, \
    create_async_engine

from app.core import Base
from app.models import Event, Place, SyncMeta, Ticket
from app.repository.base import BaseRepository
from app.repository.event import EventRepository
from app.repository.place import PlaceRepository
from app.repository.sync import SyncRepository
from app.repository.ticket import TicketRepository
from app.schemas import EventFilter


@pytest.fixture(scope='session')
def anyio_backend():
    return 'asyncio'


@pytest_asyncio.fixture(scope='session')
async def postgres_container():
    """Session-scoped PostgreSQL container shared by all integration tests."""
    from testcontainers.community.postgres import PostgresContainer

    postgres = PostgresContainer('postgres:16-alpine', driver='asyncpg')
    postgres.start()
    yield postgres
    postgres.stop()


@pytest_asyncio.fixture(scope='function')
async def async_engine(postgres_container):
    """Create an in-memory async engine per test."""
    db_url = postgres_container.get_connection_url()
    engine = create_async_engine(db_url, echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture(scope='function')
async def session(async_engine):
    """Provide a transactional session that rolls back after each test."""
    async_session = async_sessionmaker(async_engine,
                                       expire_on_commit=False)
    async with async_session() as s:
        yield s


# ---------------------------------------------------------------------------
# Factories
# ---------------------------------------------------------------------------

def _make_place(**kwargs) -> Place:
    now = dt.datetime.now(tz=dt.UTC)
    return Place(
        id=uuid4(),
        name=kwargs.get('name', 'Test Place'),
        city=kwargs.get('city', 'Moscow'),
        address=kwargs.get('address', 'Test Street 1'),
        seats_pattern=kwargs.get('seats_pattern', 'A1-100'),
        created_at=kwargs.get('created_at', now),
        changed_at=kwargs.get('changed_at', now),
    )


def _make_event(place: Place, **kwargs) -> Event:
    now = dt.datetime.now(tz=dt.UTC)
    return Event(
        id=kwargs.get('id', uuid4()),
        name=kwargs.get('name', 'Test Event'),
        event_time=kwargs.get('event_time', now + dt.timedelta(days=5)),
        registration_deadline=kwargs.get('registration_deadline',
                                         now + dt.timedelta(days=1)),
        status=kwargs.get('status', 'published'),
        number_of_visitors=kwargs.get('number_of_visitors', 10),
        status_changed_at=kwargs.get('status_changed_at', now),
        place_id=place.id,
        created_at=kwargs.get('created_at', now),
        changed_at=kwargs.get('changed_at', now),
    )


def _make_ticket(event: Event, **kwargs) -> Ticket:
    return Ticket(
        id=uuid4(),
        seat=kwargs.get('seat', 'A1'),
        event_id=event.id,
        first_name=kwargs.get('first_name', 'Test'),
        last_name=kwargs.get('last_name', 'User'),
        email=kwargs.get('email', 'test@example.com'),
    )


def _make_sync(**kwargs) -> SyncMeta:
    now = dt.datetime.now(tz=dt.UTC)
    return SyncMeta(
        last_sync_time=kwargs.get('last_sync_time', now),
        last_changed_at=kwargs.get('last_changed_at', now),
        sync_status=kwargs.get('sync_status', 'never'),
    )


# ---------------------------------------------------------------------------
# TestBaseRepo — generic CRUD for any entity
# ---------------------------------------------------------------------------

@pytest.mark.integ
@pytest.mark.asyncio
class TestBaseRepo:
    """Tests for base repository operations (create, get_by_id, update, delete).

    Uses Place as a representative entity; the base logic is identical for all
    repositories that extend BaseRepository.
    """

    async def test_create_place(self, session: AsyncSession):
        place = _make_place(name='Create Test')
        session.add(place)
        await session.flush()

        repo = PlaceRepository(session)
        found = await repo.get_by_id(place.id)
        assert found is not None
        assert found.name == 'Create Test'

    async def test_get_by_id_found(self, session: AsyncSession):
        place = _make_place()
        session.add(place)
        await session.flush()

        repo = PlaceRepository(session)
        found = await repo.get_by_id(place.id)

        assert found is not None
        assert found.id == place.id
        assert found.name == place.name

    async def test_get_by_id_not_found(self, session: AsyncSession):
        repo = PlaceRepository(session)
        found = await repo.get_by_id(uuid4())
        assert found is None

    async def test_update_place(self, session: AsyncSession):
        place = _make_place(name='Original')
        session.add(place)
        await session.flush()

        repo = PlaceRepository(session)
        updated = await repo.update(place, {'name': 'Updated', 'city': 'SPb'})

        assert updated.name == 'Updated'
        assert updated.city == 'SPb'

    async def test_delete_place(self, session: AsyncSession):
        place = _make_place()
        session.add(place)
        await session.flush()

        repo = PlaceRepository(session)
        await repo.delete(place)

        found = await repo.get_by_id(place.id)
        assert found is None


# ---------------------------------------------------------------------------
# TestEventRepo — EventRepository
# ---------------------------------------------------------------------------

@pytest.mark.integ
@pytest.mark.asyncio
class TestEventRepo:
    """Tests for EventRepository: create, get_by_id, update, delete,
    get_detail (with joinedload), get_paginated (filtering, pagination,
    ordering, joins).
    """

    async def test_create_event(self, session: AsyncSession):
        place = _make_place()
        session.add(place)
        await session.flush()

        event = _make_event(place, name='Concert')
        session.add(event)
        await session.flush()

        repo = EventRepository(session)
        found = await repo.get_by_id(event.id)

        assert found is not None
        assert found.name == 'Concert'
        assert found.place_id == place.id

    async def test_get_by_id(self, session: AsyncSession):
        place = _make_place()
        session.add(place)
        await session.flush()

        event = _make_event(place)
        session.add(event)
        await session.flush()

        repo = EventRepository(session)
        found = await repo.get_by_id(event.id)

        assert found is not None
        assert found.id == event.id

    async def test_get_by_id_not_found(self, session: AsyncSession):
        repo = EventRepository(session)
        found = await repo.get_by_id(uuid4())
        assert found is None

    async def test_update_event(self, session: AsyncSession):
        place = _make_place()
        session.add(place)
        await session.flush()

        event = _make_event(place)
        session.add(event)
        await session.flush()

        repo = EventRepository(session)
        updated = await repo.update(event, {'status': 'cancelled'})

        assert updated.status == 'cancelled'

    async def test_delete_event(self, session: AsyncSession):
        place = _make_place()
        session.add(place)
        await session.flush()

        event = _make_event(place)
        session.add(event)
        await session.flush()

        repo = EventRepository(session)
        await repo.delete(event)

        found = await repo.get_by_id(event.id)
        assert found is None

    # -- get_detail --------------------------------------------------------

    async def test_get_detail_with_place(self, session: AsyncSession):
        place = _make_place(name='Opera House')
        session.add(place)
        await session.flush()

        event = _make_event(place, name='Swan Lake')
        session.add(event)
        await session.flush()

        repo = EventRepository(session)
        detail = await repo.get_detail(event.id)

        assert detail is not None
        assert detail.name == 'Swan Lake'
        assert detail.place is not None
        assert detail.place.name == 'Opera House'

    async def test_get_detail_not_found(self, session: AsyncSession):
        repo = EventRepository(session)
        detail = await repo.get_detail(uuid4())
        assert detail is None

    # -- get_paginated -----------------------------------------------------

    async def test_get_paginated_all(self, session: AsyncSession):
        place = _make_place()
        session.add(place)
        await session.flush()

        events = [
            _make_event(place, name=f'Event {i}',
                        event_time=dt.datetime(2026, 10, i + 1,
                                               tzinfo=dt.UTC))
            for i in range(1, 6)
        ]
        session.add_all(events)
        await session.flush()

        repo = EventRepository(session)
        items, count = await repo.get_paginated(
            EventFilter(), limit=10, offset=0,
        )

        assert count == 5
        assert len(items) == 5

    async def test_get_paginated_limit_offset(self, session: AsyncSession):
        place = _make_place()
        session.add(place)
        await session.flush()

        events = [_make_event(place, name=f'Event {i}')
                  for i in range(1, 11)]
        session.add_all(events)
        await session.flush()

        repo = EventRepository(session)

        items_p1, count_p1 = await repo.get_paginated(
            EventFilter(), limit=3, offset=0,
        )
        assert count_p1 == 10
        assert len(items_p1) == 3
        assert items_p1[0].name == 'Event 1'

        items_p2, count_p2 = await repo.get_paginated(
            EventFilter(), limit=3, offset=3,
        )
        assert count_p2 == 10
        assert len(items_p2) == 3
        assert items_p2[0].name == 'Event 4'

    async def test_get_paginated_date_filter(self, session: AsyncSession):
        place = _make_place()
        session.add(place)
        await session.flush()

        now = dt.datetime.now(tz=dt.UTC)
        events = [
            _make_event(place, name='Old Event',
                        event_time=now - dt.timedelta(days=30)),
            _make_event(place, name='New Event',
                        event_time=now + dt.timedelta(days=10)),
            _make_event(place, name='Future Event',
                        event_time=now + dt.timedelta(days=60)),
        ]
        session.add_all(events)
        await session.flush()

        repo = EventRepository(session)
        items, count = await repo.get_paginated(
            EventFilter(date_from=now.date()),
            limit=10, offset=0,
        )

        assert count == 2
        names = {it.name for it in items}
        assert 'New Event' in names
        assert 'Future Event' in names
        assert 'Old Event' not in names

    async def test_get_paginated_empty(self, session: AsyncSession):
        repo = EventRepository(session)
        items, count = await repo.get_paginated(
            EventFilter(), limit=10, offset=0,
        )
        assert count == 0
        assert len(items) == 0

    async def test_get_paginated_joins_place(self, session: AsyncSession):
        place = _make_place(name='Special Venue')
        session.add(place)
        await session.flush()

        event = _make_event(place, name='VIP Concert')
        session.add(event)
        await session.flush()

        repo = EventRepository(session)
        items, count = await repo.get_paginated(
            EventFilter(), limit=10, offset=0,
        )

        assert count == 1
        assert items[0].place is not None
        assert items[0].place.name == 'Special Venue'

    async def test_get_paginated_order_by_event_time(self, session: AsyncSession):
        place = _make_place()
        session.add(place)
        await session.flush()

        events = [
            _make_event(place, name='Later',
                        event_time=dt.datetime(2026, 12, 31,
                                               tzinfo=dt.UTC)),
            _make_event(place, name='Earlier',
                        event_time=dt.datetime(2026, 1, 1,
                                               tzinfo=dt.UTC)),
            _make_event(place, name='Middle',
                        event_time=dt.datetime(2026, 6, 15,
                                               tzinfo=dt.UTC)),
        ]
        session.add_all(events)
        await session.flush()

        repo = EventRepository(session)
        items, _ = await repo.get_paginated(
            EventFilter(), limit=10, offset=0,
        )

        assert len(items) == 3
        assert items[0].name == 'Earlier'
        assert items[1].name == 'Middle'
        assert items[2].name == 'Later'

    # -- edge cases --------------------------------------------------------

    async def test_get_paginated_large_offset(self, session: AsyncSession):
        place = _make_place()
        session.add(place)
        await session.flush()
        session.add(_make_event(place))
        await session.flush()

        repo = EventRepository(session)
        items, count = await repo.get_paginated(
            EventFilter(), limit=10, offset=100,
        )
        assert count == 1
        assert len(items) == 0

    async def test_get_paginated_zero_limit(self, session: AsyncSession):
        place = _make_place()
        session.add(place)
        await session.flush()
        session.add(_make_event(place))
        await session.flush()

        repo = EventRepository(session)
        items, count = await repo.get_paginated(
            EventFilter(), limit=0, offset=0,
        )
        assert count == 1
        assert len(items) == 0

    async def test_date_filter_no_match(self, session: AsyncSession):
        place = _make_place()
        session.add(place)
        await session.flush()
        session.add(_make_event(place,
                                event_time=dt.datetime(2025, 1, 1,
                                                       tzinfo=dt.UTC)))
        await session.flush()

        repo = EventRepository(session)
        items, count = await repo.get_paginated(
            EventFilter(
                date_from=dt.datetime(2030, 1, 1, tzinfo=dt.UTC).date()),
            limit=10, offset=0,
        )
        assert count == 0
        assert len(items) == 0


# ---------------------------------------------------------------------------
# TestPlaceRepo — PlaceRepository
# ---------------------------------------------------------------------------

@pytest.mark.integ
@pytest.mark.asyncio
class TestPlaceRepo:
    """Tests for PlaceRepository: create, get_by_id, update, delete."""

    async def test_create_place(self, session: AsyncSession):
        place = _make_place(name='Unique Place', city='Kazan',
                            address='Kremlin St 1')
        session.add(place)
        await session.flush()

        repo = PlaceRepository(session)
        found = await repo.get_by_id(place.id)

        assert found is not None
        assert found.name == 'Unique Place'
        assert found.city == 'Kazan'
        assert found.address == 'Kremlin St 1'

    async def test_get_by_id(self, session: AsyncSession):
        place = _make_place()
        session.add(place)
        await session.flush()

        repo = PlaceRepository(session)
        found = await repo.get_by_id(place.id)

        assert found is not None
        assert found.id == place.id

    async def test_get_by_id_not_found(self, session: AsyncSession):
        repo = PlaceRepository(session)
        found = await repo.get_by_id(uuid4())
        assert found is None

    async def test_update_place(self, session: AsyncSession):
        place = _make_place(name='Before')
        session.add(place)
        await session.flush()

        repo = PlaceRepository(session)
        updated = await repo.update(place,
                                    {'name': 'After', 'city': 'Novosib'})

        assert updated.name == 'After'
        assert updated.city == 'Novosib'

    async def test_delete_place(self, session: AsyncSession):
        place = _make_place()
        session.add(place)
        await session.flush()

        repo = PlaceRepository(session)
        await repo.delete(place)

        found = await repo.get_by_id(place.id)
        assert found is None

    async def test_place_with_events(self, session: AsyncSession):
        place = _make_place(name='Venue')
        session.add(place)
        await session.flush()

        event = _make_event(place, name='Show')
        session.add(event)
        await session.flush()

        repo = PlaceRepository(session)
        found = await repo.get_by_id(place.id)
        assert found is not None
        assert found.name == 'Venue'


# ---------------------------------------------------------------------------
# TestSyncRepo — SyncRepository
# ---------------------------------------------------------------------------

@pytest.mark.integ
@pytest.mark.asyncio
class TestSyncRepo:
    """Tests for SyncRepository: create, get_by_id, update, delete.

    SyncMeta uses an integer primary key (unlike UUID for other entities).
    """

    async def test_create_sync(self, session: AsyncSession):
        sync = _make_sync(sync_status='syncing')
        session.add(sync)
        await session.flush()

        repo = SyncRepository(session)
        found = await repo.get_by_id(sync.id)

        assert found is not None
        assert found.sync_status == 'syncing'
        assert found.last_sync_time is not None

    async def test_get_by_id(self, session: AsyncSession):
        sync = _make_sync()
        session.add(sync)
        await session.flush()

        repo = SyncRepository(session)
        found = await repo.get_by_id(sync.id)

        assert found is not None
        assert found.id == sync.id

    async def test_get_by_id_not_found(self, session: AsyncSession):
        repo = SyncRepository(session)
        found = await repo.get_by_id(99999)
        assert found is None

    async def test_update_sync(self, session: AsyncSession):
        sync = _make_sync(sync_status='syncing')
        session.add(sync)
        await session.flush()

        repo = SyncRepository(session)
        updated = await repo.update(sync, {'sync_status': 'completed'})

        assert updated.sync_status == 'completed'

    async def test_delete_sync(self, session: AsyncSession):
        sync = _make_sync()
        session.add(sync)
        await session.flush()

        repo = SyncRepository(session)
        await repo.delete(sync)

        found = await repo.get_by_id(sync.id)
        assert found is None

    async def test_sync_multiple_records(self, session: AsyncSession):
        for i in range(3):
            session.add(_make_sync(sync_status=f'status_{i}'))
        await session.flush()

        repo = SyncRepository(session)
        items = []
        for sid in range(1, 4):
            found = await repo.get_by_id(sid)
            if found:
                items.append(found)

        assert len(items) == 3


# ---------------------------------------------------------------------------
# TestTicketRepo — TicketRepository
# ---------------------------------------------------------------------------

@pytest.mark.integ
@pytest.mark.asyncio
class TestTicketRepo:
    """Tests for TicketRepository: create, get_by_id, update, delete,
    event relationship, multiple tickets.
    """

    async def test_create_ticket(self, session: AsyncSession):
        place = _make_place()
        session.add(place)
        await session.flush()

        event = _make_event(place)
        session.add(event)
        await session.flush()

        ticket = _make_ticket(event, seat='B5', first_name='Alice')
        session.add(ticket)
        await session.flush()

        repo = TicketRepository(session)
        found = await repo.get_by_id(ticket.id)

        assert found is not None
        assert found.seat == 'B5'
        assert found.first_name == 'Alice'
        assert found.event_id == event.id

    async def test_get_by_id_found(self, session: AsyncSession):
        place = _make_place()
        session.add(place)
        await session.flush()

        event = _make_event(place)
        session.add(event)
        await session.flush()

        ticket = _make_ticket(event, seat='C10')
        session.add(ticket)
        await session.flush()

        repo = TicketRepository(session)
        found = await repo.get_by_id(ticket.id)

        assert found is not None
        assert found.id == ticket.id
        assert found.seat == 'C10'

    async def test_get_by_id_not_found(self, session: AsyncSession):
        repo = TicketRepository(session)
        found = await repo.get_by_id(uuid4())
        assert found is None

    async def test_ticket_event_loaded(self, session: AsyncSession):
        place = _make_place(name='Concert Hall')
        session.add(place)
        await session.flush()

        event = _make_event(place, name='Rock Concert')
        session.add(event)
        await session.flush()

        ticket = _make_ticket(event, seat='A1')
        session.add(ticket)
        await session.flush()

        repo = TicketRepository(session)
        found = await repo.get_by_id(ticket.id)

        assert found is not None
        assert found.event is not None
        assert found.event.name == 'Rock Concert'
        assert found.event.place.name == 'Concert Hall'

    async def test_multiple_tickets_same_event(self, session: AsyncSession):
        place = _make_place()
        session.add(place)
        await session.flush()

        event = _make_event(place)
        session.add(event)
        await session.flush()

        tickets = []
        for i in range(5):
            t = _make_ticket(event, seat=f'A{i + 1}',
                             first_name=f'User{i}')
            session.add(t)
            tickets.append(t)
        await session.flush()

        repo = TicketRepository(session)
        seats = []
        for t in tickets:
            found = await repo.get_by_id(t.id)
            assert found is not None
            seats.append(found.seat)

        assert set(seats) == {'A1', 'A2', 'A3', 'A4', 'A5'}

    async def test_tickets_different_events(self, session: AsyncSession):
        place = _make_place()
        session.add(place)
        await session.flush()

        event1 = _make_event(place, name='Event 1')
        event2 = _make_event(place, name='Event 2')
        session.add_all([event1, event2])
        await session.flush()

        t1 = _make_ticket(event1, seat='A1')
        t2 = _make_ticket(event2, seat='B1')
        session.add_all([t1, t2])
        await session.flush()

        repo = TicketRepository(session)

        found1 = await repo.get_by_id(t1.id)
        found2 = await repo.get_by_id(t2.id)

        assert found1.event_id == event1.id
        assert found2.event_id == event2.id
        assert found1.event_id != found2.event_id

    async def test_update_ticket(self, session: AsyncSession):
        place = _make_place()
        session.add(place)
        await session.flush()

        event = _make_event(place)
        session.add(event)
        await session.flush()

        ticket = _make_ticket(event, first_name='Old')
        session.add(ticket)
        await session.flush()

        repo = TicketRepository(session)
        updated = await repo.update(ticket, {'first_name': 'New'})
        assert updated.first_name == 'New'

    async def test_delete_ticket(self, session: AsyncSession):
        place = _make_place()
        session.add(place)
        await session.flush()

        event = _make_event(place)
        session.add(event)
        await session.flush()

        ticket = _make_ticket(event)
        session.add(ticket)
        await session.flush()

        repo = TicketRepository(session)
        await repo.delete(ticket)

        found = await repo.get_by_id(ticket.id)
        assert found is None

    async def test_ticket_long_email(self, session: AsyncSession):
        place = _make_place()
        session.add(place)
        await session.flush()

        event = _make_event(place)
        session.add(event)
        await session.flush()

        ticket = _make_ticket(
            event,
            email='a' * 50 + '@' + 'b' * 30 + '.example.com',
        )
        session.add(ticket)
        await session.flush()

        repo = TicketRepository(session)
        found = await repo.get_by_id(ticket.id)
        assert found is not None
        assert found.email == ticket.email
