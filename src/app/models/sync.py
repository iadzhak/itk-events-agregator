import datetime as dt

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core import Base
from app.types import SyncStatus

DEFAULT_LAST_CHANGED_AT = dt.datetime(2000, 1, 1, tzinfo=dt.UTC)
SYNC_STATUS_MAX_LENGTH = 10


class SyncMeta(Base):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    last_sync_time: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: dt.datetime.now(tz=dt.UTC)
    )
    last_changed_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), default=DEFAULT_LAST_CHANGED_AT
    )
    sync_status: Mapped[SyncStatus] = mapped_column(
        String(SYNC_STATUS_MAX_LENGTH), default=SyncStatus.NEVER
    )
