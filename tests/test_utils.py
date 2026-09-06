import datetime as dt
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.clients.events_provider import EventsProviderClient
from app.schemas import EventDB, EventsResponse
from app.utils.events_paginator import EventsPaginator


@pytest.mark.unit
class TestEventsPaginator:
    CHANGE_AT = dt.datetime(2000, 1, 1, tzinfo=dt.UTC)

    def test_get_cursor(self):
        cursor = 'xyz'
        url = f'http://test/?cursor={cursor}'
        iterator = EventsPaginator(MagicMock(), self.CHANGE_AT)
        result = iterator.get_cursor(url)
        assert isinstance(result, str)
        assert result == cursor

    @pytest.mark.asyncio
    async def test_iterator_collect_correctly(self, event_factory):
        mock_event_names = ['first', 'second']
        mock_events = [event_factory(n) for n in mock_event_names]
        first = EventsResponse(
            next='http://test/?cursor=xyz',
            previous=None,
            results=[mock_events[0]]
        )
        second = EventsResponse(
            next=None,
            previous='http://test/?cursor=zyx',
            results=[mock_events[1]]
        )
        client = MagicMock(spec=EventsProviderClient)
        client.events = AsyncMock(side_effect=[first, second, first])

        iterator = EventsPaginator(client, changed_at=self.CHANGE_AT)
        result = [e async for e in iterator]
        assert all(isinstance(e, EventDB) for e in result)
        assert len(result) == len(mock_events)
        assert result == mock_events

    @pytest.mark.asyncio
    async def test_iterator_empty(self, event_factory):
        first = EventsResponse(
            next=None,
            previous=None,
            results=[]
        )
        second = EventsResponse(
            next=None,
            previous=None,
            results=[event_factory()]
        )
        client = MagicMock(spec=EventsProviderClient)
        client.events = AsyncMock(side_effect=[first, second])
        iterator = EventsPaginator(client, changed_at=self.CHANGE_AT)
        result = [e async for e in iterator]
        assert result == []
