import datetime as dt

from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.clients import BaseProviderClient
from app.core import ExternalApiError, get_logger
from app.models import Event, Place, SyncMeta
from app.repository import BaseRepository
from app.types import SyncStatus
from app.utils import BasePaginator

logger = get_logger(__name__)


class SyncService:
    DEFAULT_ID = 1

    def __init__(
            self,
            client: BaseProviderClient,
            paginator_class: type[BasePaginator],
            sync_repo: BaseRepository[SyncMeta],
            events_repo: BaseRepository[Event],
            place_repo: BaseRepository[Place]

    ) -> None:
        self._client = client
        self._paginator_class = paginator_class
        self._sync_repo = sync_repo
        self._events_repo = events_repo
        self._place_repo = place_repo

    async def get_meta(self) -> SyncMeta:
        meta = await self._sync_repo.get_by_id(self.DEFAULT_ID)
        if meta is None:
            meta = await self._sync_repo.create({'id': self.DEFAULT_ID})
        return meta

    async def run(self, session: AsyncSession) -> dt.datetime:
        meta = await self.get_meta()
        if meta.sync_status == SyncStatus.RUNNING:
            logger.info('Синхронизация уже идет')
            return meta.last_sync_time
        now = dt.datetime.now(tz=dt.UTC)
        meta.sync_status = SyncStatus.RUNNING
        meta.last_sync_time = now
        session.add(meta)
        await session.commit()
        logger.info(f'Запущена фоновая синхронизация от {now!s}')
        try:
            last_event = await self._proceed_events(meta)
            meta.sync_status = SyncStatus.SUCCESS
            if last_event:
                meta.last_changed_at = last_event.changed_at
            session.add(meta)
        except (ExternalApiError, ValidationError):
            meta.sync_status = SyncStatus.ERROR
            logger.exception(f'Ошибка фоновой синхронизации от {now!s}')
        finally:
            await session.commit()
        logger.info(f'Завершена фоновая синхронизация от {now!s}')
        return meta.last_sync_time

    async def _proceed_db_obj(
            self,
            data: dict,
            repo: BaseRepository[Event | Place],
    ):
        db_obj = await repo.get_by_id(_id=data['id'])
        if db_obj is None:
            db_obj = await repo.create(data=data)
        if data['changed_at'] != db_obj.changed_at:
            await repo.update(db_obj=db_obj, data=data)

    async def _proceed_events(self, meta: SyncMeta):
        last_event = None
        paginator = self._paginator_class(self._client, meta.last_changed_at)

        async for event in paginator:
            # sync places
            await self._proceed_db_obj(
                data=event.place.model_dump(),
                repo=self._place_repo,
            )
            # sync events
            event_data = event.model_dump(exclude={'place'})
            event_data['place_id'] = event.place.id
            await self._proceed_db_obj(
                data=event_data,
                repo=self._events_repo,
            )
            last_event = event

        return last_event
