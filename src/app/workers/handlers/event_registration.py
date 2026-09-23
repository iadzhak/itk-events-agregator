from app.clients import BaseNotificationClient
from app.core import HandlerError, InternalApiError


class EventRegistrationHandler:
    def __init__(self, client: BaseNotificationClient) -> None:
        self.client = client

    async def handle(self, payload) -> None:
        try:
            await self.client.notify(
                msg=payload.get('message'),
                reference_id=payload.get('reference_id'),
                idempotency_key=payload.get('idempotency_key'),
            )
        except InternalApiError as e:
            raise HandlerError(str(e)) from e
