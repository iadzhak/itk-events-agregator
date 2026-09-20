import datetime as dt
from collections import deque
from collections.abc import AsyncIterator
from typing import Callable, Self, TypeAlias
from urllib.parse import parse_qs, urlparse

from app.clients import BaseProviderClient
from app.core import ExternalApiError
from app.schemas import EventDB

BasePaginatorFactory: TypeAlias = Callable[
    [BaseProviderClient, dt.datetime], AsyncIterator[EventDB]
]


class EventsPaginator(AsyncIterator[EventDB]):
    def __init__(
        self, client: BaseProviderClient, changed_at: dt.datetime
    ) -> None:
        self._client = client
        self._changed_at = changed_at
        self._buffer: deque[EventDB] = deque()
        self._cursor: str | None = None
        self._stop = False

    def __aiter__(self) -> Self:
        return self

    async def __anext__(self) -> EventDB:
        if not self._stop and not self._buffer:
            response = await self._client.events(
                changed_at=self._changed_at, cursor=self._cursor
            )
            self._buffer.extend(response.results)
            if response.next:
                self._cursor = self.get_cursor(str(response.next))
            else:
                self._stop = True

        if self._stop and not self._buffer:
            raise StopAsyncIteration

        return self._buffer.popleft()

    @staticmethod
    def get_cursor(url: str) -> str:
        parsed = urlparse(url)
        query = parse_qs(parsed.query)
        cursor = query.get('cursor')
        if cursor is None:
            raise ExternalApiError(f'No cursor in URL: {url}')
        return str(cursor[0])


def get_events_paginator_class():
    return EventsPaginator
