from app.clients import BaseNotificationClient
from app.core import HandlerError, InternalApiError


class EventRegistrationHandler:
    def __init__(self, client: BaseNotificationClient) -> None:
        self.client = client

    async def handle(self, payload) -> None:
        try:
            await self.client.notify(**payload)
        except InternalApiError as e:
            raise HandlerError(str(e)) from e
