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
def mock_handler_cls():
    handler_instance = MagicMock()
    handler_instance.handle = AsyncMock(return_value=None)
    handler_cls = MagicMock(return_value=handler_instance)
    return handler_cls


@pytest.fixture
def mock_handler_cls_raise():
    handler_instance = MagicMock()
    handler_instance.handle = AsyncMock(side_effect=HandlerError)
    handler_cls = MagicMock(return_value=handler_instance)
    return handler_cls


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
@pytest.mark.asyncio
class TestOutboxWorker:

    def test_register_handler_function(self, mock_worker, mock_handler_cls):
        mock_type = OutboxType.EVENT_REGISTRATION
        mock_worker.register_handler(mock_type)(mock_handler_cls)
        assert mock_worker._REGISTRY[mock_type] == mock_handler_cls

    def test_register_handler_decorator(self, mock_worker):
        mock_type = OutboxType.EVENT_REGISTRATION

        @OutboxWorker.register_handler(mock_type)
        class MockHandler:
            async def handle(self, payload):
                return

        assert isinstance(mock_worker._REGISTRY, dict)
        assert mock_worker._REGISTRY[mock_type] == MockHandler

    async def test_run(self, mock_worker):
        mock_worker.polling_interval_s = 0.1
        mock_worker.run_once = AsyncMock(side_effect=asyncio.CancelledError)
        await mock_worker.run()
        mock_worker.run_once.assert_awaited_once()

    async def test_run_once_handled(self, mock_sessionmaker, mock_handler_cls):
        out = _make_outbox(
            event_type=OutboxType.EVENT_REGISTRATION,
            status=OutboxStatus.PENDING,
            retry_count=0
        )
        OutboxWorker._REGISTRY[
            OutboxType.EVENT_REGISTRATION] = mock_handler_cls

        worker = OutboxWorker(0, 0, _make_repo_cls(out), mock_sessionmaker)
        await worker.run_once()
        mock_handler_cls.return_value.handle.assert_awaited_once()
        assert out.status == OutboxStatus.SENT

    async def test_run_once_not_handled(self, mock_sessionmaker,
                                        mock_handler_cls_raise):
        out = _make_outbox(
            event_type=OutboxType.EVENT_REGISTRATION,
            status=OutboxStatus.FAILED,
            retry_count=0
        )
        OutboxWorker._REGISTRY[
            OutboxType.EVENT_REGISTRATION] = mock_handler_cls_raise

        worker = OutboxWorker(0, 0, _make_repo_cls(out), mock_sessionmaker)
        await worker.run_once()
        mock_handler_cls_raise.return_value.handle.assert_awaited_once()
        assert out.status == OutboxStatus.FAILED

    async def test_run_once_retry_count_increment(self, mock_sessionmaker,
                                                  mock_handler_cls_raise):
        retries = 1
        out = _make_outbox(
            event_type=OutboxType.EVENT_REGISTRATION,
            status=OutboxStatus.FAILED,
            retry_count=retries
        )
        OutboxWorker._REGISTRY[
            OutboxType.EVENT_REGISTRATION] = mock_handler_cls_raise

        worker = OutboxWorker(0, 0, _make_repo_cls(out), mock_sessionmaker)
        await worker.run_once()
        mock_handler_cls_raise.return_value.handle.assert_awaited_once()
        assert out.status == OutboxStatus.FAILED
        assert out.retry_count == retries + 1

    async def test_run_once_retry_count_not_increment(self, mock_sessionmaker,
                                                      mock_handler_cls):
        retries = 1
        out = _make_outbox(
            event_type=OutboxType.EVENT_REGISTRATION,
            status=OutboxStatus.PENDING,
            retry_count=retries
        )
        OutboxWorker._REGISTRY[
            OutboxType.EVENT_REGISTRATION] = mock_handler_cls

        worker = OutboxWorker(0, 0, _make_repo_cls(out), mock_sessionmaker)
        await worker.run_once()
        mock_handler_cls.return_value.handle.assert_awaited_once()
        assert out.status == OutboxStatus.SENT
        assert out.retry_count == retries
