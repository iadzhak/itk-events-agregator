import datetime as dt
from uuid import UUID

from sqlalchemy.exc import IntegrityError

from app.clients import BaseProviderClient
from app.core import (
    BadRequestError,
    IdempotencyError,
    InternalError,
    NotFoundError,
    get_logger,
)
from app.models import Event
from app.repository import (
    EventRepository,
    IdempotencyRepository,
    OutboxRepository,
    TicketRepository,
)
from app.schemas import Ticket
from app.types import EventStatus, OutboxType
from app.utils import is_seat_exist, make_payload_hash

logger = get_logger(__name__)

NOTIFICATION_MSG = 'Вы успешно зарегистрированы на мероприятие - {name} {time}'


class CreateTicketUseCase:
    def __init__(
        self,
        client: BaseProviderClient,
        events: EventRepository,
        tickets: TicketRepository,
        outbox: OutboxRepository,
        idempotency: IdempotencyRepository,
    ) -> None:
        self._client = client
        self._events = events
        self._tickets = tickets
        self._outbox = outbox
        self._idempotency = idempotency

    async def do(
        self,
        event_id: UUID,
        first_name: str,
        last_name: str,
        email: str,
        seat: str,
        idempotency_key: str | None = None,
    ) -> Ticket:

        payload = {
            'event_id': event_id,
            'first_name': first_name,
            'last_name': last_name,
            'email': email,
            'seat': seat,
        }
        payload_hash = make_payload_hash(payload)

        # check idempotency
        check = await self.check_idempotency(idempotency_key, payload_hash)
        if check is not None:
            return check

        # check event
        event = await self.check_event(event_id)

        # check seats
        await self.check_seat(seat, event, event_id)

        # make request
        ticket_id = await self._client.register(
            event_id, first_name, last_name, seat, email
        )
        if ticket_id is None:
            raise BadRequestError(
                'Не удалось получить ticket_id от провайдера'
            )

        # save ticket in db
        data = {
            'id': ticket_id,
            'event_id': event_id,
            'first_name': first_name,
            'last_name': last_name,
            'email': email,
            'seat': seat,
        }
        await self._tickets.create(data)
        msg = NOTIFICATION_MSG.format(
            name=event.name, time=event.event_time.strftime('%d.%m.%Y %H:%M')
        )
        data_out_payload = {
            'message': msg,
            'reference_id': str(ticket_id),
        }

        if idempotency_key is not None:
            try:
                await self._idempotency.create(
                    {
                        'idempotency_key': idempotency_key,
                        'payload_hash': payload_hash,
                        'response': {'ticket_id': str(ticket_id)},
                    }
                )
            except IntegrityError as e:
                check = await self.check_idempotency(
                    idempotency_key, payload_hash
                )
                if check is None:
                    raise InternalError(
                        f'Ошибка добавления по '
                        f'idempotency_key: {idempotency_key}'
                    ) from e
                return check
            data_out_payload['idempotency_key'] = str(idempotency_key)

        data_out = {
            'aggregate_id': str(ticket_id),
            'event_type': OutboxType.EVENT_REGISTRATION,
            'payload': data_out_payload,
        }
        await self._outbox.create(data_out)

        # return response
        return Ticket(ticket_id=ticket_id)

    async def check_idempotency(
        self, idempotency_key: str | None, payload_hash: str
    ) -> Ticket | None:
        if idempotency_key is not None:
            idempotency = await self._idempotency.get_by_key(idempotency_key)
            if idempotency is not None:
                if idempotency.payload_hash == payload_hash:
                    return Ticket(**idempotency.response)
                else:
                    raise IdempotencyError('Конфликт данных')
        return None

    async def check_event(self, event_id: UUID) -> Event:
        # check event exist
        event: Event | None = await self._events.get_by_id(event_id)
        if event is None:
            raise NotFoundError(f'Мероприятие с id: {event_id!s} не найдено')

        # check event status is published
        if event.status != EventStatus.PUBLISHED:
            raise BadRequestError(
                f'Регистрация возможно только на мероприятия со статусом '
                f'"published". Мероприятия "{event.name}" статус '
                f'"{event.status}"'
            )

        # check event registration deadline
        now = dt.datetime.now(tz=dt.UTC)
        if now >= event.registration_deadline:
            raise BadRequestError(
                f'Регистрация на мероприятие {event.name} уже завершилась'
            )

        return event

    async def check_seat(
        self, seat: str, event: Event, event_id: UUID
    ) -> None:

        # check seat exist (seat_pattern)
        is_seat_exist(seat, event.place.seats_pattern)

        # check seat is free (internal db)
        seats_in_db = [t.seat for t in event.tickets]
        if seat in seats_in_db:
            raise BadRequestError(f'Место {seat} уже занято.')

        # check seat is free (external api)
        seats = await self._client.seats(event_id)
        if seat not in seats:
            seats_str = ','.join(seats)
            raise BadRequestError(
                f'Место {seat} уже занято. Доступные места: {seats_str}'
            )
