from fastapi import APIRouter, BackgroundTasks

from app.background_tasks import sync_meta_once

router = APIRouter()


@router.post('/trigger')
async def trigger_sync(
        background_tasks: BackgroundTasks
):
    background_tasks.add_task(sync_meta_once)
    return {'status': 'ok'}
