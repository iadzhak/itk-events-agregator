import datetime as dt
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.clients.events_provider import EventsProviderClient
from app.schemas import EventDB, EventsExternal
from app.utils import make_payload_hash
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
        first = EventsExternal(
            next='http://test/?cursor=xyz',
            previous=None,
            results=[mock_events[0]]
        )
        second = EventsExternal(
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
        first = EventsExternal(
            next=None,
            previous=None,
            results=[]
        )
        second = EventsExternal(
            next=None,
            previous=None,
            results=[event_factory()]
        )
        client = MagicMock(spec=EventsProviderClient)
        client.events = AsyncMock(side_effect=[first, second])
        iterator = EventsPaginator(client, changed_at=self.CHANGE_AT)
        result = [e async for e in iterator]
        assert result == []


@pytest.mark.unit
class TestMakePayloadHash:
    def test_returns_str(self):
        data = {'a': 'b', 'b': 'c'}
        h = make_payload_hash(data)
        assert isinstance(h, str)

    @pytest.mark.parametrize(
        'data',
        (
                {'a': 12},
                {'a': 2.25},
                {'a': 'text'},
                {'a': uuid4()},
                {'a': dt.datetime.now()},
        ),
        ids=['int', 'float', 'str', 'uuid', 'datetime']
    )
    def test_can_accept_type(self, data):
        h = make_payload_hash(data)
        assert isinstance(h, str)

    def test_differentiable(self):
        data = {'a': 'b', 'b': 'c'}
        h = make_payload_hash(data)
        for _ in range(3):
            test = make_payload_hash(data)
            assert h == test

    def test_different_order_same_hash(self):
        data_1 = {'a': 'b', 'b': 'c'}
        data_2 = {'b': 'c', 'a': 'b'}
        h1 = make_payload_hash(data_1)
        h2 = make_payload_hash(data_2)
        assert h1 == h2
