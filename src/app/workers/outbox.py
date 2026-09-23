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
        self._registry: dict[OutboxType, OutboxHandler] = {}

    def register_handler(
        self, outbox_type: OutboxType, handler: OutboxHandler
    ) -> None:
        self._registry[outbox_type] = handler

    async def run_once(self):
        async with self.session_factory() as session:
            repo = self.outbox_repo_cls(session)
            to_proceed = await repo.get_for_processing(self.max_retries)
            logger.info('В очереди на обработку %s событий', len(to_proceed))
            no_handlers = set()
            for out in to_proceed:
                handler = self._registry.get(out.event_type)
                if handler is None:
                    no_handlers.add(out.event_type)
                    continue
                try:
                    await handler.handle(out.payload)
                    out.status = OutboxStatus.SENT
                    logger.info(
                        'Успешно обработано %s сообщение %s',
                        out.event_type,
                        out.id,
                    )
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
                except Exception as e:
                    out.status = OutboxStatus.FAILED
                    out.retry_count += 1
                    out.error_message = str(e)
                    logger.exception(
                        'Неожиданная ошибка при обработке %s события %s: %s',
                        out.event_type,
                        out.id,
                        str(e),
                    )
            if no_handlers:
                logger.warning(
                    'Для %s не назначены обработчики', ', '.join(no_handlers)
                )
            logger.info(
                'Коммит транзакции с изменениями %s событий', len(to_proceed)
            )
            await session.commit()
            logger.info('Транзакция успешно закоммичена')

    async def run(self):
        logger.info('Outbox worker запущен')
        while True:
            try:
                await self.run_once()
                await asyncio.sleep(self.polling_interval_s)
            except asyncio.CancelledError:
                break
        logger.info('Outbox worker завершил работу')
