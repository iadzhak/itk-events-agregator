import datetime as dt
from uuid import UUID


class CommonMixin:
    id: UUID
    name: str
    changed_at: dt.datetime
    created_at: dt.datetime
