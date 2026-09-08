import datetime as dt
from uuid import uuid4

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.clients import BaseProviderClient, EventsProviderClient
from app.core import BadRequestError, ExternalApiError, NotFoundError
from app.flows import CancelTicketUseCase, CreateTicketUseCase
from app.repository import EventRepository, TicketRepository
from app.schemas import CancelTicket, Ticket
from app.types import EventStatus


# ---------------------------------------------------------------------------
# Fixtures — mock repos and client
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_client():
    client = MagicMock(spec=BaseProviderClient)
    client.seats = AsyncMock(return_value=['A1', 'A2', 'A3'])
    client.register = AsyncMock(return_value=uuid4())
    client.cancel = AsyncMock(return_value=True)
    return client


@pytest.fixture
def mock_event_repo():
    repo = MagicMock(spec=EventRepository)
    repo.get_by_id = AsyncMock(return_value=None)
    return repo


@pytest.fixture
def mock_ticket_repo():
    repo = MagicMock(spec=TicketRepository)
    repo.get_by_id = AsyncMock(return_value=None)
    repo.create = AsyncMock()
    repo.delete = AsyncMock()
    return repo


# ---------------------------------------------------------------------------
# Helpers — build minimal event/ticket domain objects
# ---------------------------------------------------------------------------

def _make_event(**kwargs):
    from app.schemas import PlaceDB

    now = dt.datetime.now(tz=dt.UTC)
    return type('Event', (), {
        'id': kwargs.get('id', uuid4()),
        'name': kwargs.get('name', 'Test Event'),
        'status': kwargs.get('status', EventStatus.PUBLISHED),
        'event_time': kwargs.get('event_time', now + dt.timedelta(days=5)),
        'registration_deadline': kwargs.get(
            'registration_deadline', now + dt.timedelta(days=1),
        ),
        'place': kwargs.get(
            'place',
            PlaceDB(
                id=uuid4(),
                name='Hall',
                city='Moscow',
                address='Main St 1',
                seats_pattern='A1-10,B1-10',
                created_at=now,
                changed_at=now,
            ),
        ),
        'tickets': kwargs.get('tickets', []),
    })


def _make_ticket(event, **kwargs):
    from app.models import Ticket as TicketModel

    ticket = type('Ticket', (), {
        'id': kwargs.get('id', uuid4()),
        'seat': kwargs.get('seat', 'A1'),
        'event_id': event.id,
        'first_name': kwargs.get('first_name', 'First'),
        'last_name': kwargs.get('last_name', 'Last'),
        'email': kwargs.get('email', 'test@example.com'),
        'event': event,
    })
    return ticket


# ---------------------------------------------------------------------------
# TestCreateTicketUseCase
# ---------------------------------------------------------------------------

@pytest.mark.unit
@pytest.mark.asyncio
class TestCreateTicketUseCase:
    """Tests for CreateTicketUseCase covering happy path and all error paths."""

    async def test_happy_path(self, mock_client, mock_event_repo, mock_ticket_repo):
        event = _make_event()
        mock_event_repo.get_by_id.return_value = event

        case = CreateTicketUseCase(mock_client, mock_event_repo, mock_ticket_repo)
        result = await case.do(
            event_id=event.id,
            first_name='John',
            last_name='Doe',
            email='john@example.com',
            seat='A1',
        )

        assert isinstance(result, Ticket)
        mock_client.seats.assert_called_once_with(event.id)
        mock_client.register.assert_called_once_with(
            event.id, 'John', 'Doe', 'A1', 'john@example.com',
        )
        mock_ticket_repo.create.assert_called_once()
        call_args = mock_ticket_repo.create.call_args[0][0]
        assert call_args['ticket_id'] == mock_client.register.return_value
        assert call_args['seat'] == 'A1'

    # -- event not found ---------------------------------------------------

    async def test_event_not_found(self, mock_client, mock_event_repo, mock_ticket_repo):
        mock_event_repo.get_by_id.return_value = None

        case = CreateTicketUseCase(mock_client, mock_event_repo, mock_ticket_repo)

        with pytest.raises(NotFoundError, match='не найдено'):
            await case.do(uuid4(), 'F', 'L', 'e@e.com', 'A1')

        mock_client.seats.assert_not_called()
        mock_client.register.assert_not_called()

    # -- event not published -----------------------------------------------

    async def test_event_not_published(self, mock_client, mock_event_repo, mock_ticket_repo):
        event = _make_event(status='draft')
        mock_event_repo.get_by_id.return_value = event

        case = CreateTicketUseCase(mock_client, mock_event_repo, mock_ticket_repo)

        with pytest.raises(BadRequestError, match='только на мероприятия со статусом "published"'):
            await case.do(event.id, 'F', 'L', 'e@e.com', 'A1')

        mock_client.seats.assert_not_called()

    # -- registration deadline passed --------------------------------------

    async def test_registration_deadline_passed(self, mock_client, mock_event_repo, mock_ticket_repo):
        now = dt.datetime.now(tz=dt.UTC)
        event = _make_event(registration_deadline=now - dt.timedelta(days=1))
        mock_event_repo.get_by_id.return_value = event

        case = CreateTicketUseCase(mock_client, mock_event_repo, mock_ticket_repo)

        with pytest.raises(BadRequestError, match='уже завершилась'):
            await case.do(event.id, 'F', 'L', 'e@e.com', 'A1')

        mock_client.seats.assert_not_called()

    # -- seat not in pattern -----------------------------------------------

    async def test_seat_not_in_pattern(self, mock_client, mock_event_repo, mock_ticket_repo):
        event = _make_event()
        mock_event_repo.get_by_id.return_value = event

        case = CreateTicketUseCase(mock_client, mock_event_repo, mock_ticket_repo)

        with pytest.raises(BadRequestError, match='Секции Z нет среди доступных'):
            await case.do(event.id, 'F', 'L', 'e@e.com', 'Z1')

        mock_client.seats.assert_not_called()

    # -- seat number out of range ------------------------------------------

    async def test_seat_number_out_of_range(self, mock_client, mock_event_repo, mock_ticket_repo):
        event = _make_event()
        mock_event_repo.get_by_id.return_value = event

        case = CreateTicketUseCase(mock_client, mock_event_repo, mock_ticket_repo)

        with pytest.raises(BadRequestError, match='нет среди возможных'):
            await case.do(event.id, 'F', 'L', 'e@e.com', 'A999')

        mock_client.seats.assert_not_called()

    # -- seat already taken in internal db ---------------------------------

    async def test_seat_taken_in_db(self, mock_client, mock_event_repo, mock_ticket_repo):
        event = _make_event()
        existing_ticket = _make_ticket(event, seat='A1')
        event.tickets = [existing_ticket]
        mock_event_repo.get_by_id.return_value = event

        case = CreateTicketUseCase(mock_client, mock_event_repo, mock_ticket_repo)

        with pytest.raises(BadRequestError, match='уже занято'):
            await case.do(event.id, 'F', 'L', 'e@e.com', 'A1')

        mock_client.seats.assert_not_called()

    # -- seat not available from external provider -------------------------

    async def test_seat_not_available_external(self, mock_client, mock_event_repo, mock_ticket_repo):
        event = _make_event()
        mock_event_repo.get_by_id.return_value = event
        mock_client.seats.return_value = ['A2', 'A3']  # A1 not available

        case = CreateTicketUseCase(mock_client, mock_event_repo, mock_ticket_repo)

        with pytest.raises(BadRequestError, match='уже занято. Доступные места'):
            await case.do(event.id, 'F', 'L', 'e@e.com', 'A1')

        mock_client.register.assert_not_called()

    # -- provider returns no ticket_id -------------------------------------

    async def test_provider_returns_no_ticket_id(self, mock_client, mock_event_repo, mock_ticket_repo):
        event = _make_event()
        mock_event_repo.get_by_id.return_value = event
        mock_client.register.return_value = None

        case = CreateTicketUseCase(mock_client, mock_event_repo, mock_ticket_repo)

        with pytest.raises(BadRequestError, match='Не удалось получить ticket_id'):
            await case.do(event.id, 'F', 'L', 'e@e.com', 'A1')

        mock_ticket_repo.create.assert_not_called()


# ---------------------------------------------------------------------------
# TestCancelTicketUseCase
# ---------------------------------------------------------------------------

@pytest.mark.unit
@pytest.mark.asyncio
class TestCancelTicketUseCase:
    """Tests for CancelTicketUseCase covering happy path and all error paths."""

    async def test_happy_path(self, mock_client, mock_ticket_repo):
        event = _make_event()
        ticket = _make_ticket(event, seat='A1')
        mock_ticket_repo.get_by_id.return_value = ticket

        case = CancelTicketUseCase(mock_client, mock_ticket_repo)
        result = await case.do(ticket.id)

        assert isinstance(result, CancelTicket)
        assert result.success is True
        mock_client.cancel.assert_called_once_with(event.id, ticket.id)
        mock_ticket_repo.delete.assert_called_once_with(ticket)

    # -- ticket not found --------------------------------------------------

    async def test_ticket_not_found(self, mock_client, mock_ticket_repo):
        mock_ticket_repo.get_by_id.return_value = None

        case = CancelTicketUseCase(mock_client, mock_ticket_repo)

        with pytest.raises(NotFoundError, match='не найден'):
            await case.do(uuid4())

        mock_client.cancel.assert_not_called()

    # -- event already passed ----------------------------------------------

    async def test_event_already_passed(self, mock_client, mock_ticket_repo):
        event = _make_event(event_time=dt.datetime.now(tz=dt.UTC) - dt.timedelta(days=1))
        ticket = _make_ticket(event)
        mock_ticket_repo.get_by_id.return_value = ticket

        case = CancelTicketUseCase(mock_client, mock_ticket_repo)

        with pytest.raises(BadRequestError, match='уже прошло'):
            await case.do(ticket.id)

        mock_client.cancel.assert_not_called()

    # -- external api returns false ----------------------------------------

    async def test_external_api_returns_false(self, mock_client, mock_ticket_repo):
        event = _make_event()
        ticket = _make_ticket(event)
        mock_ticket_repo.get_by_id.return_value = ticket
        mock_client.cancel.return_value = False

        case = CancelTicketUseCase(mock_client, mock_ticket_repo)

        with pytest.raises(ExternalApiError, match='Не удалось отменить регистрацию'):
            await case.do(ticket.id)

        mock_ticket_repo.delete.assert_not_called()
