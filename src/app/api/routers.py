from fastapi import APIRouter

from app.api.endpoints.events import router as events_router
from app.api.endpoints.health import router as health_router
from app.api.endpoints.sync import router as sync_router
from app.api.endpoints.tickets import router as tickets_router

main_router = APIRouter(prefix='/api')
main_router.include_router(
    events_router,
    prefix='/events',
    tags=['events']
)
main_router.include_router(
    tickets_router,
    prefix='/tickets',
    tags=['tickets']
)
main_router.include_router(
    health_router,
    tags=['health']
)
main_router.include_router(
    sync_router,
    prefix='/sync',
    tags=['sync']
)
