import datetime as dt

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core import BaseInt
from app.types import OutboxStatus, OutboxType


class Outbox(BaseInt):
    event_type: Mapped[OutboxType] = mapped_column(String, nullable=False)
    aggregate_id: Mapped[str | None] = mapped_column(String, nullable=True)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    status: Mapped[OutboxStatus] = mapped_column(
        String, default=OutboxStatus.PENDING, nullable=False, index=True
    )
    retry_count: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )
    error_message: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: dt.datetime.now(tz=dt.timezone.utc),
        nullable=False,
        index=True,
    )
    last_changed_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: dt.datetime.now(tz=dt.timezone.utc),
        onupdate=lambda: dt.datetime.now(tz=dt.timezone.utc),
        nullable=False,
    )
