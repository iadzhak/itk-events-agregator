from fastapi import APIRouter

from app.api.endpoints import (
    events_router,
    health_router,
    sync_router,
    tickets_router,
)

main_router = APIRouter(prefix='/api')
main_router.include_router(events_router, prefix='/events', tags=['events'])
main_router.include_router(tickets_router, prefix='/tickets', tags=['tickets'])
main_router.include_router(health_router, tags=['health'])
main_router.include_router(sync_router, prefix='/sync', tags=['sync'])
