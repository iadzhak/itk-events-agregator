from fastapi import APIRouter

router = APIRouter()


@router.post('/trigger')
async def trigger_sync():
    return None
