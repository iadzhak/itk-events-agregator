import asyncio
from unittest.mock import MagicMock, AsyncMock, Mock
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.models import Outbox
from app.workers.outbox import OutboxHandler, OutboxWorker
from app.types import OutboxType, OutboxStatus
from app.repository import OutboxRepository
from app.core import HandlerError


@pytest.fixture
def mock_handler():
    handler = MagicMock(spec=OutboxHandler)
    handler.handle = AsyncMock(return_value=None)
    return handler


@pytest.fixture
def mock_handler_raise():
    handler = MagicMock(spec=OutboxHandler)
    handler.handle = AsyncMock(side_effect=HandlerError)
    return handler


@pytest.fixture
def mock_sessionmaker():
    return MagicMock(spec=async_sessionmaker)


def _make_repo_cls(return_value):
    mock_repo_instance = AsyncMock()
    mock_repo_instance.get_for_processing = AsyncMock(
        return_value=[return_value])
    mock_repo_cls = MagicMock(return_value=mock_repo_instance)
    return mock_repo_cls


@pytest.fixture
def mock_worker(mock_sessionmaker):
    return OutboxWorker(0, 0, OutboxRepository, mock_sessionmaker)


def _make_outbox(**kwargs) -> Outbox:
    payload = {
        'message': 'Hello',
        'reference_id': str(uuid4()),
        'idempotency_key': str(uuid4())
    }
    return Outbox(
        event_type=kwargs.get('event_type', OutboxType.EVENT_REGISTRATION),
        aggregate_id=kwargs.get('aggregate_id', str(uuid4())),
        payload=kwargs.get('payload', payload),
        status=kwargs.get('status', OutboxStatus.PENDING),
        retry_count=kwargs.get('retry_count', 0),
        last_changed_at=kwargs.get('last_changed_at', None)
    )


@pytest.mark.unit
class TestOutboxWorker:

    def test_register_handler_function(self, mock_worker, mock_handler):
        mock_type = OutboxType.EVENT_REGISTRATION
        mock_worker.register_handler(mock_type, mock_handler)
        assert mock_worker._registry[mock_type] == mock_handler

    @pytest.mark.asyncio
    async def test_run(self, mock_worker):
        mock_worker.polling_interval_s = 0.1
        mock_worker.run_once = AsyncMock(side_effect=asyncio.CancelledError)
        await mock_worker.run()
        mock_worker.run_once.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_run_once_handled(self, mock_sessionmaker, mock_handler):
        out = _make_outbox(
            event_type=OutboxType.EVENT_REGISTRATION,
            status=OutboxStatus.PENDING,
            retry_count=0
        )

        worker = OutboxWorker(0, 0, _make_repo_cls(out), mock_sessionmaker)
        worker._registry[OutboxType.EVENT_REGISTRATION] = mock_handler
        await worker.run_once()
        mock_handler.handle.assert_awaited_once()
        assert out.status == OutboxStatus.SENT

    @pytest.mark.asyncio
    async def test_run_once_not_handled(self, mock_sessionmaker,
                                        mock_handler_raise):
        out = _make_outbox(
            event_type=OutboxType.EVENT_REGISTRATION,
            status=OutboxStatus.FAILED,
            retry_count=0
        )

        worker = OutboxWorker(0, 0, _make_repo_cls(out), mock_sessionmaker)
        worker._registry[OutboxType.EVENT_REGISTRATION] = mock_handler_raise
        await worker.run_once()
        mock_handler_raise.handle.assert_awaited_once()
        assert out.status == OutboxStatus.FAILED

    @pytest.mark.asyncio
    async def test_run_once_retry_count_increment(self, mock_sessionmaker,
                                                  mock_handler_raise):
        retries = 1
        out = _make_outbox(
            event_type=OutboxType.EVENT_REGISTRATION,
            status=OutboxStatus.FAILED,
            retry_count=retries
        )

        worker = OutboxWorker(0, 0, _make_repo_cls(out), mock_sessionmaker)
        worker._registry[OutboxType.EVENT_REGISTRATION] = mock_handler_raise
        await worker.run_once()
        mock_handler_raise.handle.assert_awaited_once()
        assert out.status == OutboxStatus.FAILED
        assert out.retry_count == retries + 1

    @pytest.mark.asyncio
    async def test_run_once_retry_count_not_increment(self, mock_sessionmaker,
                                                      mock_handler):
        retries = 1
        out = _make_outbox(
            event_type=OutboxType.EVENT_REGISTRATION,
            status=OutboxStatus.PENDING,
            retry_count=retries
        )

        worker = OutboxWorker(0, 0, _make_repo_cls(out), mock_sessionmaker)
        worker._registry[OutboxType.EVENT_REGISTRATION] = mock_handler
        await worker.run_once()
        mock_handler.handle.assert_awaited_once()
        assert out.status == OutboxStatus.SENT
        assert out.retry_count == retries
