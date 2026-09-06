__all__ = [
    'events_router',
    'health_router',
    'sync_router',
    'tickets_router'
]

from app.api.endpoints.events import router as events_router
from app.api.endpoints.health import router as health_router
from app.api.endpoints.sync import router as sync_router
from app.api.endpoints.tickets import router as tickets_router
