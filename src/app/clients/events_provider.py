import datetime as dt
from collections.abc import Coroutine
from types import TracebackType
from typing import Any, Self
from uuid import UUID

from httpx import AsyncClient, AsyncHTTPTransport, HTTPError, Response

from app.clients.base import BaseProviderClient
from app.core import ExternalApiError
from app.metrics import (
    events_provider_request_duration_seconds,
    events_provider_requests_total,
)
from app.schemas import EventsExternal


class EventsProviderClient(BaseProviderClient):
    EVENTS_URL = '/api/events/'
    SEATS_URL = '/api/events/{event_id}/seats/'
    REGISTER_URL = '/api/events/{event_id}/register/'
    CANCEL_URL = '/api/events/{event_id}/unregister/'

    def __init__(self, base_url: str, api_key: str, retries: int) -> None:
        self.headers = {'x-api-key': api_key}
        self.base_url = base_url
        self.retries = retries
        self._client = AsyncClient(
            base_url=self.base_url,
            headers=self.headers,
            follow_redirects=True,
            transport=AsyncHTTPTransport(retries=self.retries),
        )

    async def __aenter__(self) -> Self:
        self._client = AsyncClient(
            base_url=self.base_url,
            headers=self.headers,
            follow_redirects=True,
            transport=AsyncHTTPTransport(retries=self.retries),
        )
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ):
        if self._client:
            await self._client.aclose()

    async def _handle_response(
        self, endpoint: str, request: Coroutine[Any, Any, Response]
    ) -> Response:
        try:
            with events_provider_request_duration_seconds.labels(
                endpoint=endpoint
            ).time():
                response = await request
            events_provider_requests_total.labels(
                endpoint=endpoint, status=response.status_code
            )
            response.raise_for_status()
            return response
        except HTTPError as e:
            raise ExternalApiError('Ошибка работы с внешним API') from e

    async def events(
        self, changed_at: dt.datetime, cursor: str | None = None
    ) -> EventsExternal:
        params = {'changed_at': changed_at.strftime('%Y-%m-%d')}
        if cursor is not None:
            params['cursor'] = cursor
        request = self._client.get(self.EVENTS_URL, params=params)
        response = await self._handle_response(self.EVENTS_URL, request)
        data = response.json()
        return EventsExternal(**data)

    async def seats(self, event_id: UUID) -> list[str]:
        url = self.SEATS_URL.format(event_id=str(event_id))
        request = self._client.get(url)
        response = await self._handle_response(self.SEATS_URL, request)
        data = response.json()
        return data.get('seats', [])

    async def register(
        self,
        event_id: UUID,
        first_name: str,
        last_name: str,
        seat: str,
        email: str,
    ) -> UUID:
        url = self.REGISTER_URL.format(event_id=str(event_id))
        body = {
            'first_name': first_name,
            'last_name': last_name,
            'seat': seat,
            'email': email,
        }
        request = self._client.post(url, json=body)
        response = await self._handle_response(self.REGISTER_URL, request)
        data = response.json()
        ticket_id = data.get('ticket_id')
        if ticket_id is None:
            raise ExternalApiError(
                f'Провайдер не вернул ticket_id в ответе: {data}'
            )
        return UUID(ticket_id)

    async def cancel(self, event_id: UUID, ticket_id: UUID) -> bool:
        body = {'ticket_id': str(ticket_id)}
        request = self._client.request(
            'DELETE', self.CANCEL_URL.format(event_id=str(event_id)), json=body
        )
        response = await self._handle_response(self.CANCEL_URL, request)
        data = response.json()
        return data.get('success', False)

    async def aclose(self) -> None:
        await self._client.aclose()
