from fastapi import APIRouter

router = APIRouter()


@router.post('/')
async def register_for_event():
    return None


@router.delete('/{ticket_id}')
async def cancel_registration():
    return None
