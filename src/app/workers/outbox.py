import asyncio
from typing import Protocol

from sqlalchemy.ext.asyncio import async_sessionmaker

from app.core import HandlerError, get_logger
from app.repository import OutboxRepository
from app.types import OutboxStatus, OutboxType

logger = get_logger(__name__)


class OutboxHandler(Protocol):
    async def handle(self, payload) -> None: ...


class OutboxWorker:
    _REGISTRY: dict[OutboxType, type[OutboxHandler]] = {}

    def __init__(
        self,
        polling_interval_s: int,
        max_retries: int,
        outbox_repo_cls: type[OutboxRepository],
        session_factory: async_sessionmaker,
    ):
        self.session_factory = session_factory
        self.polling_interval_s = polling_interval_s
        self.outbox_repo_cls = outbox_repo_cls
        self.max_retries = max_retries

    @classmethod
    def register_handler(cls, outbox_type: OutboxType):

        def wrapper(handler_cls: type[OutboxHandler]):
            cls._REGISTRY[outbox_type] = handler_cls
            return handler_cls

        return wrapper

    async def run_once(self):
        async with self.session_factory() as session:
            repo = self.outbox_repo_cls(session)
            to_proceed = await repo.get_for_processing(self.max_retries)
            no_handlers = set()
            handled = 0
            total = len(to_proceed)
            for out in to_proceed:
                handler_cls = self._REGISTRY.get(out.event_type)
                if handler_cls is None:
                    no_handlers.add(out.event_type)
                    continue
                handler = handler_cls()
                try:
                    await handler.handle(out.payload)
                    out.status = OutboxStatus.SENT
                    handled += 1
                except HandlerError as e:
                    out.status = OutboxStatus.FAILED
                    out.retry_count += 1
                    out.error_message = str(e)
                    logger.warning(
                        'Не удалось выполнить обработку %s события: %s. %s',
                        out.event_type,
                        out.id,
                        str(e),
                    )
            if no_handlers:
                logger.warning(
                    'Для %s не назначены обработчики', ', '.join(no_handlers)
                )
            if handled > 0:
                logger.info(
                    'Успешно обработано %s исходящих событий из %s',
                    handled,
                    total,
                )
            await session.commit()

    async def run(self):
        while True:
            try:
                await self.run_once()
                await asyncio.sleep(self.polling_interval_s)
            except asyncio.CancelledError:
                break
