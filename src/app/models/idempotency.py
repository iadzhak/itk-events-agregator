import datetime as dt

from sqlalchemy import DateTime, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core import BaseInt


class Idempotency(BaseInt):
    idempotency_key: Mapped[str] = mapped_column(
        String, unique=True, nullable=False, index=True
    )
    payload_hash: Mapped[str] = mapped_column(String, nullable=False)
    response: Mapped[dict] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: dt.datetime.now(tz=dt.timezone.utc),
        nullable=False,
    )
