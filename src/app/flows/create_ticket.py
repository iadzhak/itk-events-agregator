import datetime as dt
import re
from uuid import UUID

from app.clients import BaseProviderClient
from app.core import BadRequestError, NotFoundError
from app.repository import EventRepository, TicketRepository
from app.schemas import Ticket
from app.types import EventStatus


class CreateTicketUseCase:
    def __init__(
        self,
        client: BaseProviderClient,
        events: EventRepository,
        tickets: TicketRepository,
    ) -> None:
        self._client = client
        self._events = events
        self._tickets = tickets

    async def do(
        self,
        event_id: UUID,
        first_name: str,
        last_name: str,
        email: str,
        seat: str,
    ) -> Ticket:
        event = await self._events.get_by_id(event_id)

        # check event exist
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

        # check seat exist (seat_pattern)
        self.is_seat_exist(seat, event.place.seats_pattern)

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

        # return response
        return Ticket(ticket_id=ticket_id)

    def is_seat_exist(self, seat: str, seats_pattern: str):
        range_pattern = re.compile(r'([A-Z])(\d+)-(\d+)')
        place_pattern = re.compile(r'([A-Z])(\d+)')
        parts = seats_pattern.split(',')
        available = {}
        for part in parts:
            m = range_pattern.match(part)
            section, min_place, max_place = m.groups()
            available[section] = int(min_place), int(max_place)
        s, p = place_pattern.match(seat).groups()
        p = int(p)
        if s not in available:
            all_s = ','.join(available.keys())
            raise BadRequestError(f'Секции {s} нет среди доступных: {all_s}')
        if p < available[s][0] or p > available[s][1]:
            raise BadRequestError(
                f'Места {p} нет среди возможных '
                f'{available[s][0]}-{available[s][1]} для секции {s}'
            )
