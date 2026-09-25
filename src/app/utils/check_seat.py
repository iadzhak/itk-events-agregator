import re

from app.core import BadRequestError, InternalError, get_logger

logger = get_logger(__name__)

RANGE_PATTERN = re.compile(r'([A-Z])(\d+)-(\d+)')
PLACE_PATTERN = re.compile(r'([A-Z])(\d+)')


def is_seat_exist(seat: str, seats_pattern: str):
    parts = seats_pattern.split(',')
    available = {}
    for part in parts:
        m = RANGE_PATTERN.match(part)
        if m is None:
            logger.error('Некорректный seats_pattern: %s', seats_pattern)
            raise InternalError('Ошибка чтения мест на мероприятии')
        section, min_place, max_place = m.groups()
        available[section] = int(min_place), int(max_place)
    m_seats = PLACE_PATTERN.match(seat)
    if m_seats is None:
        raise BadRequestError(f'Неверный формат диапазона мест: {seat!r}')
    s, p = m_seats.groups()
    p = int(p)
    if s not in available:
        all_s = ','.join(available.keys())
        raise BadRequestError(f'Секции {s} нет среди доступных: {all_s}')
    if p < available[s][0] or p > available[s][1]:
        raise BadRequestError(
            f'Места {p} нет среди возможных '
            f'{available[s][0]}-{available[s][1]} для секции {s}'
        )
