import datetime as dt
from uuid import UUID

from httpx import AsyncClient

from app.clients.base import BaseProviderClient
from app.schemas.external import EventsResponse


class EventsProviderClient(BaseProviderClient):
    EVENTS_URL = '/api/events/'
    SEATS_URL = '/api/events/{event_id}/seats/'
    REGISTER_URL = '/api/events/{event_id}/register/'
    CANCEL_URL = '/api/events/{event_id}/unregister/'

    def __init__(self, base_url: str, api_key: str) -> None:
        headers = {
            'x-api-key': api_key
        }
        self._client = AsyncClient(base_url=base_url, headers=headers)

    async def events(
            self,
            changed_at: dt.datetime,
            cursor: str | None = None
    ) -> EventsResponse:
        params = {'changed_at': changed_at.strftime('%Y-%m-%d')}
        if cursor is not None:
            params['cursor'] = cursor
        response = await self._client.get(self.EVENTS_URL, params=params)
        response.raise_for_status()
        data = response.json()
        return EventsResponse(**data)

    async def seats(self, event_id: UUID) -> list[str]:
        url = self.SEATS_URL.format(event_id=str(event_id))
        response = await self._client.get(url)
        response.raise_for_status()
        data = response.json()
        return data.get('seats', [])

    async def register(
            self,
            event_id: UUID,
            first_name: str,
            last_name: str,
            seat: str,
            email: str
    ) -> UUID:
        url = self.REGISTER_URL.format(event_id=str(event_id))
        body = {
            'first_name': first_name,
            'last_name': last_name,
            'seat': seat,
            'email': email
        }
        response = await self._client.post(url, json=body)
        response.raise_for_status()
        data = response.json()
        return UUID(data.get('ticket_id'))

    async def cancel(self, event_id: UUID, ticket_id: UUID) -> bool:
        body = {
            'ticket_id': str(ticket_id)
        }
        response = await self._client.delete(
            self.CANCEL_URL.format(event_id=str(event_id)),
            json=body
        )
        response.raise_for_status()
        data = response.json()
        return data.get('success', False)
