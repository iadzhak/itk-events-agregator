from fastapi import APIRouter

from app.dependencies import CreateTicketUseCaseDep
from app.schemas import UserBuyTicket

router = APIRouter()


@router.post('/')
async def register_for_event(
        form: UserBuyTicket,
        usecase: CreateTicketUseCaseDep,
):
    return await usecase.do(**form.model_dump())


@router.delete('/{ticket_id}')
async def cancel_registration():
    return None
