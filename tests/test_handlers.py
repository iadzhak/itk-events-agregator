from unittest.mock import MagicMock, AsyncMock

import pytest

from app.clients import BaseNotificationClient
from app.core import HandlerError, InternalApiError
from app.workers.handlers import EventRegistrationHandler


@pytest.fixture
def mock_client():
    return AsyncMock(spec=BaseNotificationClient)


@pytest.mark.unit
@pytest.mark.asyncio
class TestEventRegistrationHandler:
    async def test_success(self, mock_client):
        handler = EventRegistrationHandler(mock_client)
        await handler.handle({'msg': 'jjg'})
        mock_client.notify.assert_awaited_once()

    async def test_raises_handler_error(self, mock_client):
        mock_client.notify.side_effect = InternalApiError
        handler = EventRegistrationHandler(mock_client)
        with pytest.raises(HandlerError):
            await handler.handle({'msg': 'jjg'})
        mock_client.notify.assert_awaited_once()
