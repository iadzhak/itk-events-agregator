from fastapi import APIRouter

router = APIRouter()


@router.get('/')
async def get_all_events():
    return None


@router.get('/{event_id}')
async def get_event_details(event_id):
    return None


@router.get('/{event_id}/seats')
async def get_available_seats(event_id):
    return None
