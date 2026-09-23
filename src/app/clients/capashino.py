from uuid import UUID

from httpx import AsyncClient, AsyncHTTPTransport, HTTPError

from app.clients.base import BaseNotificationClient
from app.core import InternalApiError


class CapashinoClient(BaseNotificationClient):
    HEADERS_JSON = {'Content-Type': 'application/json'}
    NOTIFY_URL = '/api/notifications'

    def __init__(self, base_url: str, api_key: str, retries: int) -> None:
        self._client = AsyncClient(
            base_url=base_url,
            headers={'X-API-Key': api_key},
            follow_redirects=True,
            transport=AsyncHTTPTransport(retries=retries),
        )

    async def notify(
        self,
        msg: str,
        reference_id: str | UUID,
        idempotency_key: str | UUID | None = None,
    ) -> None:
        body = {'message': msg, 'reference_id': str(reference_id)}
        if idempotency_key is not None:
            body['idempotency_key'] = str(idempotency_key)
        async with self._client as client:
            try:
                response = await client.post(self.NOTIFY_URL, json=body)
            except HTTPError as e:
                raise InternalApiError(str(e)) from e

            match response.status_code:
                case 201:
                    return
                case 400:
                    raise InternalApiError('Нет reference_id, невалидное тело')
                case 401:
                    raise InternalApiError('Нет/неверный X-API-Key')
                case 409:
                    raise InternalApiError(
                        f'Уже есть уведомление с таким '
                        f'idempotency_key: {idempotency_key}'
                    )
                case 422:
                    raise InternalApiError('Пустое message')
                case code if code >= 500:
                    raise InternalApiError(
                        'Повторная попытка со стороны воркера'
                    )
                case code:
                    raise InternalApiError(
                        f'Неизвестная ошибка status_code: {code}, '
                        f'response: {response.json()}'
                    )
