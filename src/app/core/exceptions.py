from fastapi import status


class BaseError(Exception):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    detail = 'Внутренняя ошибка сервера'

    def __init__(self, detail: str | None = None):
        self.detail = detail or self.detail


class NotFoundError(BaseError):
    status_code = status.HTTP_404_NOT_FOUND


class BadRequestError(BaseError):
    status_code = status.HTTP_400_BAD_REQUEST


class InternalError(BaseError):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR


class ExternalApiError(Exception):
    """Ошибка внешнего API клиента"""


class HandlerError(Exception):
    """Не смогли обработать исходящие событие"""
