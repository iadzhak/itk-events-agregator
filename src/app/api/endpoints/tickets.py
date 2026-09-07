from fastapi import APIRouter, status

from app.dependencies import CreateTicketUseCaseDep
from app.schemas import Ticket, UserBuyTicket

router = APIRouter()


@router.post('', status_code=status.HTTP_201_CREATED, response_model=Ticket)
async def register_for_event(
        form: UserBuyTicket,
        service: CreateTicketUseCaseDep,
):
    return await service.do(**form.model_dump())


@router.delete('/{ticket_id}')
async def cancel_registration():
    return None
