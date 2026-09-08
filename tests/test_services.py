import datetime as dt
from typing import Any
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from cachetools import TTLCache

from app.clients import BaseProviderClient
from app.core import BadRequestError, NotFoundError
from app.repository import EventRepository
from app.schemas import (
    EventDB,
    EventFilter,
    EventOut,
    PaginatedResponse,
    Pagination,
    PlaceDB,
)
from app.services.event import EventService
from app.services.sync import SyncService
from app.types import EventStatus, SyncStatus
from app.utils import BasePaginator


# =============================================================================
# EventService tests
# =============================================================================


@pytest.mark.unit
@pytest.mark.asyncio
class TestEventService:
    """Тесты для EventService с мокированными зависимостями."""

    def _make_service(
        self,
        client_mock: BaseProviderClient | None = None,
        repo_mock: EventRepository | None = None,
        cache_mock: TTLCache | None = None,
    ) -> EventService:
        if client_mock is None:
            client_mock = MagicMock(spec=BaseProviderClient)
        if repo_mock is None:
            repo_mock = MagicMock(spec=EventRepository)
        if cache_mock is None:
            cache_mock = TTLCache(maxsize=30, ttl=30)
        return EventService(
            client=client_mock,
            repo=repo_mock,
            cache=cache_mock,
        )

    # -- get --

    async def test_get_returns_event_out(self):
        event_id = uuid4()
        place = PlaceDB(
            id=uuid4(),
            name='place',
            city='city',
            address='addr',
            seats_pattern='A1',
            changed_at=dt.datetime.now(tz=dt.UTC),
            created_at=dt.datetime.now(tz=dt.UTC),
        )
        db_event = EventDB(
            id=event_id,
            name='event',
            place=place,
            event_time=dt.datetime.now(tz=dt.UTC),
            registration_deadline=dt.datetime.now(tz=dt.UTC),
            status=EventStatus.PUBLISHED,
            number_of_visitors=10,
            changed_at=dt.datetime.now(tz=dt.UTC),
            created_at=dt.datetime.now(tz=dt.UTC),
            status_changed_at=dt.datetime.now(tz=dt.UTC),
        )

        repo_mock = MagicMock(spec=EventRepository)
        repo_mock.get_by_id = AsyncMock(return_value=db_event)
        service = self._make_service(repo_mock=repo_mock)

        result = await service.get(event_id)

        assert isinstance(result, EventOut)
        assert result.id == event_id
        assert result.name == 'event'
        repo_mock.get_by_id.assert_awaited_once_with(event_id)

    async def test_get_raises_not_found_when_event_missing(self):
        event_id = uuid4()
        repo_mock = MagicMock(spec=EventRepository)
        repo_mock.get_by_id = AsyncMock(return_value=None)
        service = self._make_service(repo_mock=repo_mock)

        with pytest.raises(
            NotFoundError, match=f'Мероприятие id "{event_id!s}" не найдено'
        ):
            await service.get(event_id)

    # -- get_paginated --

    async def test_get_paginated_returns_paginated_response(self):
        place = PlaceDB(
            id=uuid4(),
            name='place',
            city='city',
            address='addr',
            seats_pattern='A1',
            changed_at=dt.datetime.now(tz=dt.UTC),
            created_at=dt.datetime.now(tz=dt.UTC),
        )
        db_event = EventDB(
            id=uuid4(),
            name='event',
            place=place,
            event_time=dt.datetime.now(tz=dt.UTC),
            registration_deadline=dt.datetime.now(tz=dt.UTC),
            status=EventStatus.PUBLISHED,
            number_of_visitors=5,
            changed_at=dt.datetime.now(tz=dt.UTC),
            created_at=dt.datetime.now(tz=dt.UTC),
            status_changed_at=dt.datetime.now(tz=dt.UTC),
        )

        repo_mock = MagicMock(spec=EventRepository)
        repo_mock.get_paginated = AsyncMock(return_value=([db_event], 1))

        request_mock = MagicMock()
        request_mock.url.include_query_params.return_value = str(
            'http://test/events?page=2'
        )

        service = self._make_service(repo_mock=repo_mock)
        filters = EventFilter()
        pagination = Pagination(page=1, page_size=10)

        result = await service.get_paginated(filters, pagination, request_mock)

        assert isinstance(result, PaginatedResponse)
        assert result.count == 1
        assert len(result.results) == 1
        assert isinstance(result.results[0], EventOut)
        repo_mock.get_paginated.assert_awaited_once_with(
            filters=filters, limit=10, offset=0
        )

    async def test_get_paginated_next_url_when_more_pages(self):
        place = PlaceDB(
            id=uuid4(),
            name='place',
            city='city',
            address='addr',
            seats_pattern='A1',
            changed_at=dt.datetime.now(tz=dt.UTC),
            created_at=dt.datetime.now(tz=dt.UTC),
        )
        db_event = EventDB(
            id=uuid4(),
            name='event',
            place=place,
            event_time=dt.datetime.now(tz=dt.UTC),
            registration_deadline=dt.datetime.now(tz=dt.UTC),
            status=EventStatus.PUBLISHED,
            number_of_visitors=5,
            changed_at=dt.datetime.now(tz=dt.UTC),
            created_at=dt.datetime.now(tz=dt.UTC),
            status_changed_at=dt.datetime.now(tz=dt.UTC),
        )

        repo_mock = MagicMock(spec=EventRepository)
        repo_mock.get_paginated = AsyncMock(return_value=([db_event], 25))

        request_mock = MagicMock()
        request_mock.url.include_query_params.return_value = str(
            'http://test/events?page=2'
        )

        service = self._make_service(repo_mock=repo_mock)
        filters = EventFilter()
        pagination = Pagination(page=1, page_size=10)

        result = await service.get_paginated(filters, pagination, request_mock)

        assert result.next is not None

    async def test_get_paginated_previous_url_on_page_gt_1(self):
        place = PlaceDB(
            id=uuid4(),
            name='place',
            city='city',
            address='addr',
            seats_pattern='A1',
            changed_at=dt.datetime.now(tz=dt.UTC),
            created_at=dt.datetime.now(tz=dt.UTC),
        )
        db_event = EventDB(
            id=uuid4(),
            name='event',
            place=place,
            event_time=dt.datetime.now(tz=dt.UTC),
            registration_deadline=dt.datetime.now(tz=dt.UTC),
            status=EventStatus.PUBLISHED,
            number_of_visitors=5,
            changed_at=dt.datetime.now(tz=dt.UTC),
            created_at=dt.datetime.now(tz=dt.UTC),
            status_changed_at=dt.datetime.now(tz=dt.UTC),
        )

        repo_mock = MagicMock(spec=EventRepository)
        repo_mock.get_paginated = AsyncMock(return_value=([db_event], 10))

        request_mock = MagicMock()
        request_mock.url.include_query_params.return_value = str(
            'http://test/events?page=1'
        )

        service = self._make_service(repo_mock=repo_mock)
        filters = EventFilter()
        pagination = Pagination(page=2, page_size=10)

        result = await service.get_paginated(filters, pagination, request_mock)

        assert result.previous is not None

    # -- get_available_seats --

    async def test_get_available_seats_returns_seats_for_published_event(self):
        event_id = uuid4()
        place = PlaceDB(
            id=uuid4(),
            name='place',
            city='city',
            address='addr',
            seats_pattern='A1',
            changed_at=dt.datetime.now(tz=dt.UTC),
            created_at=dt.datetime.now(tz=dt.UTC),
        )
        db_event = EventDB(
            id=event_id,
            name='event',
            place=place,
            event_time=dt.datetime.now(tz=dt.UTC),
            registration_deadline=dt.datetime.now(tz=dt.UTC),
            status=EventStatus.PUBLISHED,
            number_of_visitors=5,
            changed_at=dt.datetime.now(tz=dt.UTC),
            created_at=dt.datetime.now(tz=dt.UTC),
            status_changed_at=dt.datetime.now(tz=dt.UTC),
        )

        client_mock = MagicMock(spec=BaseProviderClient)
        client_mock.seats = AsyncMock(return_value=['A1', 'A2', 'B1'])

        repo_mock = MagicMock(spec=EventRepository)
        repo_mock.get_by_id = AsyncMock(return_value=db_event)

        cache_mock = TTLCache(maxsize=30, ttl=30)
        service = self._make_service(
            client_mock=client_mock, repo_mock=repo_mock, cache_mock=cache_mock
        )

        result = await service.get_available_seats(event_id)

        assert result == ['A1', 'A2', 'B1']
        client_mock.seats.assert_awaited_once_with(event_id)
        assert event_id in cache_mock

    async def test_get_available_seats_raises_for_non_published_event(self):
        event_id = uuid4()
        place = PlaceDB(
            id=uuid4(),
            name='place',
            city='city',
            address='addr',
            seats_pattern='A1',
            changed_at=dt.datetime.now(tz=dt.UTC),
            created_at=dt.datetime.now(tz=dt.UTC),
        )
        db_event = EventDB(
            id=event_id,
            name='event',
            place=place,
            event_time=dt.datetime.now(tz=dt.UTC),
            registration_deadline=dt.datetime.now(tz=dt.UTC),
            status=EventStatus.NEW,
            number_of_visitors=5,
            changed_at=dt.datetime.now(tz=dt.UTC),
            created_at=dt.datetime.now(tz=dt.UTC),
            status_changed_at=dt.datetime.now(tz=dt.UTC),
        )

        repo_mock = MagicMock(spec=EventRepository)
        repo_mock.get_by_id = AsyncMock(return_value=db_event)
        service = self._make_service(repo_mock=repo_mock)

        with pytest.raises(
            BadRequestError,
            match='статусом "published"',
        ):
            await service.get_available_seats(event_id)

    # -- get_available_seats_cached --

    async def test_get_available_seats_cached_returns_from_cache(self):
        event_id = uuid4()
        place = PlaceDB(
            id=uuid4(),
            name='place',
            city='city',
            address='addr',
            seats_pattern='A1',
            changed_at=dt.datetime.now(tz=dt.UTC),
            created_at=dt.datetime.now(tz=dt.UTC),
        )
        db_event = EventDB(
            id=event_id,
            name='event',
            place=place,
            event_time=dt.datetime.now(tz=dt.UTC),
            registration_deadline=dt.datetime.now(tz=dt.UTC),
            status=EventStatus.PUBLISHED,
            number_of_visitors=5,
            changed_at=dt.datetime.now(tz=dt.UTC),
            created_at=dt.datetime.now(tz=dt.UTC),
            status_changed_at=dt.datetime.now(tz=dt.UTC),
        )

        client_mock = MagicMock(spec=BaseProviderClient)
        client_mock.seats = AsyncMock(return_value=['A1', 'A2'])

        repo_mock = MagicMock(spec=EventRepository)
        repo_mock.get_by_id = AsyncMock(return_value=db_event)

        cache_mock = TTLCache(maxsize=30, ttl=30)
        service = self._make_service(
            client_mock=client_mock, repo_mock=repo_mock, cache_mock=cache_mock
        )

        # First call — populates cache
        result = await service.get_available_seats_cached(event_id)
        assert result.event_id == event_id
        assert result.available_seats == ['A1', 'A2']

        # Second call — uses cache, client.seats not called again
        client_mock.seats.reset_mock()
        result2 = await service.get_available_seats_cached(event_id)
        assert result2.available_seats == ['A1', 'A2']
        client_mock.seats.assert_not_awaited()


# =============================================================================
# SyncService tests
# =============================================================================


@pytest.mark.unit
@pytest.mark.asyncio
class TestSyncService:
    """Тесты для SyncService с мокированными зависимостями."""

    def _make_service(
        self,
        client_mock: BaseProviderClient | None = None,
        paginator_class_mock: type[BasePaginator] | None = None,
        sync_repo_mock: Any = None,
        events_repo_mock: Any = None,
        place_repo_mock: Any = None,
    ) -> SyncService:
        if client_mock is None:
            client_mock = MagicMock(spec=BaseProviderClient)
        if paginator_class_mock is None:
            paginator_class_mock = MagicMock(spec=type[BasePaginator])
        if sync_repo_mock is None:
            sync_repo_mock = MagicMock()
        if events_repo_mock is None:
            events_repo_mock = MagicMock()
        if place_repo_mock is None:
            place_repo_mock = MagicMock()

        return SyncService(
            client=client_mock,
            paginator_class=paginator_class_mock,
            sync_repo=sync_repo_mock,
            events_repo=events_repo_mock,
            place_repo=place_repo_mock,
        )

    # -- get_meta --

    async def test_get_meta_returns_existing_meta(self):
        meta = MagicMock()
        meta.sync_status = SyncStatus.NEVER
        meta.last_sync_time = dt.datetime.now(tz=dt.UTC)

        sync_repo_mock = MagicMock()
        sync_repo_mock.get_by_id = AsyncMock(return_value=meta)

        service = self._make_service(sync_repo_mock=sync_repo_mock)
        result = await service.get_meta()

        assert result is meta
        sync_repo_mock.get_by_id.assert_awaited_once_with(
            SyncService.DEFAULT_ID)

    async def test_get_meta_creates_meta_when_none(self):
        sync_repo_mock = MagicMock()
        sync_repo_mock.get_by_id = AsyncMock(return_value=None)
        sync_repo_mock.create = AsyncMock()
        new_meta = MagicMock()
        sync_repo_mock.create.return_value = new_meta

        service = self._make_service(sync_repo_mock=sync_repo_mock)
        result = await service.get_meta()

        assert result is new_meta
        sync_repo_mock.get_by_id.assert_awaited_once_with(
            SyncService.DEFAULT_ID)
        sync_repo_mock.create.assert_awaited_once_with(
            {'id': SyncService.DEFAULT_ID})

    # -- run (happy path) --

    async def test_run_returns_last_sync_time_on_first_sync(self):
        now = dt.datetime.now(tz=dt.UTC)
        meta = MagicMock()
        meta.sync_status = SyncStatus.NEVER
        meta.last_sync_time = None

        sync_repo_mock = MagicMock()
        sync_repo_mock.get_by_id = AsyncMock(return_value=meta)
        sync_repo_mock.update = AsyncMock()

        events_repo_mock = MagicMock()
        events_repo_mock.get_by_id = AsyncMock(return_value=None)
        events_repo_mock.create = AsyncMock()
        events_repo_mock.update = AsyncMock()

        place_repo_mock = MagicMock()
        place_repo_mock.get_by_id = AsyncMock(return_value=None)
        place_repo_mock.create = AsyncMock()
        place_repo_mock.update = AsyncMock()

        # Mock paginator to yield no events (empty sync)
        paginator_mock = AsyncMock()
        paginator_mock.__aiter__ = MagicMock(return_value=paginator_mock)
        paginator_mock.__anext__ = AsyncMock(side_effect=StopAsyncIteration)

        paginator_class_mock = MagicMock(return_value=paginator_mock)

        service = self._make_service(
            sync_repo_mock=sync_repo_mock,
            events_repo_mock=events_repo_mock,
            place_repo_mock=place_repo_mock,
            paginator_class_mock=paginator_class_mock,
        )

        result = await service.run()

        assert result == meta.last_sync_time
        meta.sync_status = SyncStatus.SUCCESS
        sync_repo_mock.update.assert_called()

    async def test_run_returns_last_sync_time_when_already_running(self):
        now = dt.datetime.now(tz=dt.UTC)
        meta = MagicMock()
        meta.sync_status = SyncStatus.RUNNING
        meta.last_sync_time = now

        sync_repo_mock = MagicMock()
        sync_repo_mock.get_by_id = AsyncMock(return_value=meta)

        service = self._make_service(sync_repo_mock=sync_repo_mock)
        result = await service.run()

        assert result == now
        sync_repo_mock.update.assert_not_called()

    async def test_run_sets_error_status_on_exception(self):
        now = dt.datetime.now(tz=dt.UTC)
        meta = MagicMock()
        meta.sync_status = SyncStatus.NEVER
        meta.last_sync_time = None

        sync_repo_mock = MagicMock()
        sync_repo_mock.get_by_id = AsyncMock(return_value=meta)
        sync_repo_mock.update = AsyncMock()

        from app.core import ExternalApiError

        paginator_mock = AsyncMock()
        paginator_mock.__aiter__ = MagicMock(return_value=paginator_mock)
        paginator_mock.__anext__ = AsyncMock(
            side_effect=ExternalApiError('API down')
        )

        paginator_class_mock = MagicMock(return_value=paginator_mock)

        service = self._make_service(
            sync_repo_mock=sync_repo_mock,
            paginator_class_mock=paginator_class_mock,
        )

        await service.run()

        assert meta.sync_status == SyncStatus.ERROR

    async def test_run_calls_place_and_event_repo_for_each_event(self):
        now = dt.datetime.now(tz=dt.UTC)
        meta = MagicMock()
        meta.sync_status = SyncStatus.NEVER
        meta.last_sync_time = now
        meta.last_changed_at = now

        sync_repo_mock = MagicMock()
        sync_repo_mock.get_by_id = AsyncMock(return_value=meta)
        sync_repo_mock.update = AsyncMock()

        events_repo_mock = MagicMock()
        events_repo_mock.get_by_id = AsyncMock(return_value=None)
        events_repo_mock.create = AsyncMock()
        events_repo_mock.update = AsyncMock()

        place_repo_mock = MagicMock()
        place_repo_mock.get_by_id = AsyncMock(return_value=None)
        place_repo_mock.create = AsyncMock()
        place_repo_mock.update = AsyncMock()

        # Create a mock event to yield from paginator
        place_obj = PlaceDB(
            id=uuid4(),
            name='place',
            city='city',
            address='addr',
            seats_pattern='A1',
            changed_at=now,
            created_at=now,
        )
        mock_event = EventDB(
            id=uuid4(),
            name='event',
            place=place_obj,
            event_time=now,
            registration_deadline=now,
            status=EventStatus.PUBLISHED,
            number_of_visitors=5,
            changed_at=now,
            created_at=now,
            status_changed_at=now,
        )

        paginator_mock = AsyncMock()
        paginator_mock.__aiter__ = MagicMock(return_value=paginator_mock)
        paginator_mock.__anext__ = AsyncMock(
            side_effect=[mock_event, StopAsyncIteration])

        paginator_class_mock = MagicMock(return_value=paginator_mock)

        service = self._make_service(
            sync_repo_mock=sync_repo_mock,
            events_repo_mock=events_repo_mock,
            place_repo_mock=place_repo_mock,
            paginator_class_mock=paginator_class_mock,
        )

        await service.run()

        # Place repo should be called for each event
        assert place_repo_mock.get_by_id.await_count >= 1
        assert events_repo_mock.get_by_id.await_count >= 1

    async def test_run_updates_last_changed_at_with_last_event(self):
        now = dt.datetime.now(tz=dt.UTC)
        meta = MagicMock()
        meta.sync_status = SyncStatus.NEVER
        meta.last_sync_time = now
        meta.last_changed_at = now - dt.timedelta(days=1)

        sync_repo_mock = MagicMock()
        sync_repo_mock.get_by_id = AsyncMock(return_value=meta)
        sync_repo_mock.update = AsyncMock()

        events_repo_mock = MagicMock()
        events_repo_mock.get_by_id = AsyncMock(return_value=None)
        events_repo_mock.create = AsyncMock()
        events_repo_mock.update = AsyncMock()

        place_repo_mock = MagicMock()
        place_repo_mock.get_by_id = AsyncMock(return_value=None)
        place_repo_mock.create = AsyncMock()
        place_repo_mock.update = AsyncMock()

        place_obj = PlaceDB(
            id=uuid4(),
            name='place',
            city='city',
            address='addr',
            seats_pattern='A1',
            changed_at=now,
            created_at=now,
        )
        mock_event = EventDB(
            id=uuid4(),
            name='event',
            place=place_obj,
            event_time=now,
            registration_deadline=now,
            status=EventStatus.PUBLISHED,
            number_of_visitors=5,
            changed_at=now,
            created_at=now,
            status_changed_at=now,
        )

        paginator_mock = AsyncMock()
        paginator_mock.__aiter__ = MagicMock(return_value=paginator_mock)
        paginator_mock.__anext__ = AsyncMock(
            side_effect=[mock_event, StopAsyncIteration])
        paginator_class_mock = MagicMock(return_value=paginator_mock)

        service = self._make_service(
            sync_repo_mock=sync_repo_mock,
            events_repo_mock=events_repo_mock,
            place_repo_mock=place_repo_mock,
            paginator_class_mock=paginator_class_mock,
        )

        await service.run()

        assert meta.last_changed_at == now
