class ExternalApiError(Exception):
    """Ошибка внешнего API клиента"""


class EventBaseException(Exception):
    pass


class EventNotFound(EventBaseException):
    """Мероприятие не найдено"""


class EventUnexpectedStatus(EventBaseException):
    """Несоответствующий статус мероприятия"""


class EventRegistrationDeadline(EventBaseException):
    """Регистрация на мероприятие уже завершилась"""


class EventUnavailableSeat(EventBaseException):
    """Недопустимое место"""


class EventPassed(Exception):
    """Мероприятие уже завершилось"""


class TicketNotFound(Exception):
    """Билета нет в базе"""
