import datetime as dt
from unittest.mock import patch, MagicMock, AsyncMock
from uuid import uuid4

import pytest
import pytest_asyncio
from fastapi import BackgroundTasks, status
from httpx import AsyncClient, ASGITransport

from app.dependencies import get_events_service, get_create_ticket_use_case, \
    get_cancel_ticket_use_case
from app.flows import CreateTicketUseCase, CancelTicketUseCase
from app.main import app
from app.services import EventService
from app.schemas import (
    EventOut, EventSeatsResponse,
    PaginatedResponse,
    PlaceFull,
    CancelTicket, Ticket, UserBuyTicket
)


# Factories

def make_PlaceOut(**kwargs):
    return PlaceFull(
        id=kwargs.get('id') or uuid4(),
        name=kwargs.get('name') or 'TestPlace',
        city=kwargs.get('city') or 'TestCity',
        address=kwargs.get('address') or 'TestAddress',
        seats_pattern=kwargs.get('seats_pattern') or 'A1-100,B1-40'
    )


def make_EventOut(**kwargs):
    default_event_time = dt.datetime.now(tz=dt.UTC)
    default_registration_deadline = dt.datetime.now(tz=dt.UTC) - dt.timedelta(
        days=1)
    return EventOut(
        id=kwargs.get('id') or uuid4(),
        name=kwargs.get('name') or 'TestEvent',
        place=kwargs.get('place') or make_PlaceOut(),
        event_time=kwargs.get('event_time') or default_event_time,
        registration_deadline=kwargs.get(
            'registration_deadline') or default_registration_deadline,
        status=kwargs.get('status') or 'published',
        number_of_visitors=kwargs.get('number_of_visitors') or 5
    )


def make_EventSeatsResponse(**kwargs):
    return EventSeatsResponse(
        event_id=kwargs.get('event_id') or uuid4(),
        available_seats=kwargs.get('available_seats') or ['A1', 'B3'],
    )


def make_UserBuyTicket(**kwargs):
    return dict(
        first_name=kwargs.get('first_name') or 'Name',
        last_name=kwargs.get('last_name') or 'Last',
        email=kwargs.get('email') or 'test@test.com',
        event_id=kwargs.get('event_id') or str(uuid4()),
        seat=kwargs.get('seat') or 'A10'
    )


def make_CancelTicket(**kwargs):
    return CancelTicket(success=kwargs.get('success') or True)


def make_Ticket(**kwargs):
    return Ticket(ticket_id=kwargs.get('ticket_id') or uuid4())


# Dependencies override

def override_get_events_service():
    service = MagicMock(spec=EventService)
    service.get_paginated = AsyncMock(
        return_value=PaginatedResponse(
            count=1,
            next=None,
            previous=None,
            results=[make_EventOut()]
        )
    )
    service.get = AsyncMock(return_value=make_EventOut())
    service.get_available_seats_cached = AsyncMock(
        return_value=make_EventSeatsResponse())
    return service


def override_get_create_ticket_use_case():
    service = MagicMock(spec=CreateTicketUseCase)
    service.do = AsyncMock(return_value=make_Ticket())
    return service


def override_get_cancel_ticket_use_case():
    service = MagicMock(spec=CancelTicketUseCase)
    service.do = AsyncMock(return_value=make_CancelTicket())
    return service


# Fixtures

@pytest_asyncio.fixture
async def test_client():
    app.dependency_overrides[get_events_service] = override_get_events_service
    app.dependency_overrides[
        get_create_ticket_use_case] = override_get_create_ticket_use_case
    app.dependency_overrides[
        get_cancel_ticket_use_case] = override_get_cancel_ticket_use_case
    async with AsyncClient(
        transport=ASGITransport(app), base_url='http://test'
    ) as c:
        yield c


# Tests

@pytest.mark.unit
@pytest.mark.asyncio
class TestHealthAPI:
    URL = '/api/health'

    async def test_success(self, test_client):
        response = await test_client.get(self.URL)
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {'status': 'ok'}


@pytest.mark.unit
@pytest.mark.asyncio
class TestSyncAPI:
    URL = '/api/sync/trigger'

    async def test_success(self, test_client):
        with patch.object(BackgroundTasks, 'add_task') as mock_add:
            response = await test_client.post(self.URL)
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {'status': 'ok'}


@pytest.mark.unit
@pytest.mark.asyncio
class TestEventsAPI:
    URL_ALL = '/api/events'
    URL_DETAIL = '/api/events/{event_id}'
    URL_SEATS = '/api/events/{event_id}/seats'

    async def test_get_all_events_success(self, test_client):
        response = await test_client.get(self.URL_ALL)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        keys = {'count', 'next', 'previous', 'results'}
        assert set(data.keys()) == keys
        assert isinstance(data['results'], list)

    async def test_get_event_details_success(self, test_client):
        url = self.URL_DETAIL.format(event_id=str(uuid4()))
        response = await test_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        event_keys = {'id', 'name', 'place', 'event_time',
                      'registration_deadline',
                      'status', 'number_of_visitors'}
        assert set(data.keys()) == event_keys
        place_keys = {'id', 'name', 'city', 'address', 'seats_pattern'}
        assert set(data['place'].keys()) == place_keys

    async def test_get_available_seats_success(self, test_client):
        url = self.URL_SEATS.format(event_id=str(uuid4()))
        response = await test_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        keys = {'event_id', 'available_seats'}
        assert set(data.keys()) == keys


@pytest.mark.unit
@pytest.mark.asyncio
class TestTicketsAPI:
    URL_REGISTER = '/api/tickets'
    URL_CANCEL = '/api/tickets/{ticket_id}'

    async def test_register_for_event_success(self, test_client):
        json = make_UserBuyTicket()
        response = await test_client.post(self.URL_REGISTER, json=json)
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        keys = {'ticket_id'}
        assert set(data.keys()) == keys

    async def test_cancel_registration_success(self, test_client):
        url = self.URL_CANCEL.format(ticket_id=str(uuid4()))
        response = await test_client.delete(url)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data == {'success': True}
