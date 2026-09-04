from fastapi import APIRouter

router = APIRouter()


@router.post('/')
async def signup_for_event():
    return None


@router.delete('/{ticket_id}')
async def cancel_signup():
    return None
