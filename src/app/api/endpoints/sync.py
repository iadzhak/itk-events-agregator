from fastapi import APIRouter, BackgroundTasks

from app.dependencies import SessionDep, SyncServiceDep

router = APIRouter()


@router.post('/trigger')
async def trigger_sync(
        session: SessionDep,
        service: SyncServiceDep,
        background_tasks: BackgroundTasks
):
    background_tasks.add_task(service.run, session)
    return 'Planned'
