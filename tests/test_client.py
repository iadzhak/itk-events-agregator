import datetime as dt
from typing import Literal
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest
from httpx import HTTPError

from app.clients.events_provider import EventsProviderClient
from app.core import ExternalApiError
from app.schemas import EventsExternal


@pytest.mark.unit
@pytest.mark.asyncio
class TestEventsProviderClient:
    BASE_URL = 'http://test'
    API_KEY = 'test'

    EVENTS_URL = '/api/events/'
    SEATS_URL = '/api/events/{event_id}/seats/'
    REGISTER_URL = '/api/events/{event_id}/register/'
    CANCEL_URL = '/api/events/{event_id}/unregister/'

    CHANGE_AT = dt.datetime(2000, 1, 1, tzinfo=dt.UTC)

    def make_body(self):
        return {
            'first_name': "John",
            'last_name': "Doe",
            'seat': "A1",
            'email': "test@test.com"
        }

    def make_client(
            self,
            response,
            method: Literal['get', 'post', 'request']
    ):
        client = EventsProviderClient(
            base_url=self.BASE_URL,
            api_key=self.API_KEY
        )
        mock_response = MagicMock()
        mock_response.json.return_value = response
        setattr(client._client, method, AsyncMock(return_value=mock_response))
        return client

    def make_client_with_raises(self, method):
        client = EventsProviderClient(
            base_url=self.BASE_URL,
            api_key=self.API_KEY
        )
        setattr(
            client._client,
            method,
            AsyncMock(side_effect=HTTPError('err'))
        )
        return client

    def make_event(self):
        return {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "name": "Конференция по Python",
            "place": {
                "id": "650e8400-e29b-41d4-a716-446655440001",
                "name": "Конференц-зал Технопарк",
                "city": "Москва",
                "address": "ул. Ленина, д. 1",
                "seats_pattern": "A1-1000,B1-2000",
                "changed_at": "2025-01-01T03:00:00+03:00",
                "created_at": "2025-01-01T03:00:00+03:00"
            },
            "event_time": "2026-01-11T17:00:00+03:00",
            "registration_deadline": "2026-01-10T17:00:00+03:00",
            "status": "published",
            "number_of_visitors": 5,
            "changed_at": "2026-01-04T22:28:35.325270+03:00",
            "created_at": "2026-01-04T22:28:35.325302+03:00",
            "status_changed_at": "2026-01-04T22:28:35.325386+03:00"
        }

    def make_seats(self):
        seats = ["A1", "A3", "A4", "A5", "A10", "B1", "B2", "B15"]
        return {'seats': seats}

    def make_ticket(self):
        return {'ticket_id': str(uuid4())}

    def make_events_response(self, results: list[dict] | None = None):
        return {
            "next": "http://...api/events?changed_at=2026-01-01&cursor=xyz",
            "previous": None,
            "results": results or []
        }

    def make_cancel(self):
        return {'success': True}

    @pytest.mark.parametrize(
        'mock_date, mock_cursor',
        (
                ('2000-01-01', None),
                ('2000-01-01', 'xyz'),
        ),
        ids=['no cursor', 'with cursor']
    )
    async def test_events_query_params(self, mock_date, mock_cursor):
        client = self.make_client(
            response=self.make_events_response(),
            method='get'
        )
        await client.events(
            changed_at=dt.datetime.fromisoformat(mock_date),
            cursor=mock_cursor
        )
        check_params = {
            'changed_at': mock_date
        }
        if mock_cursor is not None:
            check_params['cursor'] = mock_cursor
        client._client.get.assert_awaited_once_with(
            self.EVENTS_URL,
            params=check_params
        )

    async def test_events_returns_pydantic_model(self):
        client = self.make_client(
            response=self.make_events_response(
                results=[self.make_event()]
            ),
            method='get'
        )
        response = await client.events(changed_at=self.CHANGE_AT)
        assert isinstance(response, EventsExternal)
        assert len(response.results) == 1

    async def test_events_return_empty_results(self):
        client = self.make_client(
            response=self.make_events_response(),
            method='get'
        )
        response = await client.events(changed_at=self.CHANGE_AT)
        assert isinstance(response, EventsExternal)
        assert isinstance(response.results, list)
        assert len(response.results) == 0

    async def test_events_http_error(self):
        client = self.make_client_with_raises('get')
        with pytest.raises(ExternalApiError):
            await client.events(changed_at=self.CHANGE_AT)

    async def test_seats_correct_url(self):
        mock_uuid = uuid4()
        client = self.make_client(
            response=self.make_seats(),
            method='get'
        )
        await client.seats(event_id=mock_uuid)
        client._client.get.assert_awaited_once_with(
            client.SEATS_URL.format(event_id=mock_uuid),
        )

    async def test_seats_success(self):
        mock_seats = self.make_seats()
        client = self.make_client(
            response=self.make_seats(),
            method='get'
        )
        response = await client.seats(event_id=uuid4())
        assert isinstance(response, list)
        assert response == mock_seats['seats']

    async def test_seats_return_empty_list(self):
        client = self.make_client(
            response={},
            method='get'
        )
        response = await client.seats(event_id=uuid4())
        assert isinstance(response, list)
        assert len(response) == 0

    async def test_seats_http_error(self):
        client = self.make_client_with_raises('get')
        with pytest.raises(ExternalApiError):
            await client.seats(event_id=uuid4())

    async def test_register_correct_url_and_body(self):
        mock_event_id = uuid4()
        mock_body = self.make_body()
        client = self.make_client(
            response=self.make_ticket(),
            method='post'
        )
        await client.register(
            event_id=mock_event_id,
            **mock_body
        )
        client._client.post.assert_awaited_once_with(
            self.REGISTER_URL.format(event_id=mock_event_id),
            json=mock_body
        )

    async def test_register_return_uuid(self):
        mock_ticket = self.make_ticket()
        client = self.make_client(
            response=mock_ticket,
            method='post'
        )
        response = await client.register(
            event_id=uuid4(),
            **self.make_body()
        )
        assert isinstance(response, UUID)
        assert response == UUID(mock_ticket['ticket_id'])

    async def test_register_http_error(self):
        client = self.make_client_with_raises('get')
        with pytest.raises(ExternalApiError):
            await client.register(
                event_id=uuid4(),
                **self.make_body()
            )

    async def test_cancel_correct_url_and_body(self):
        client = self.make_client(
            response=self.make_cancel(),
            method='request'
        )
        mock_event_id = uuid4()
        mock_ticket = self.make_ticket()
        await client.cancel(
            event_id=mock_event_id,
            ticket_id=UUID(mock_ticket['ticket_id'])
        )
        client._client.request.assert_awaited_once_with(
            'DELETE',
            self.CANCEL_URL.format(event_id=mock_event_id),
            json=mock_ticket
        )

    async def test_cancel_success(self):
        client = self.make_client(
            response=self.make_cancel(),
            method='request'
        )
        response = await client.cancel(
            event_id=uuid4(),
            ticket_id=uuid4()
        )
        assert response is True

    async def test_cancel_http_error(self):
        client = self.make_client_with_raises('request')
        with pytest.raises(ExternalApiError):
            await client.cancel(
                event_id=uuid4(),
                ticket_id=uuid4()
            )
