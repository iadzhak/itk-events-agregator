from uuid import UUID

from fastapi import APIRouter, status

from app.dependencies import CancelTicketUseCaseDep, CreateTicketUseCaseDep
from app.schemas import CancelTicket, Ticket, UserBuyTicket

router = APIRouter()


@router.post('', status_code=status.HTTP_201_CREATED, response_model=Ticket)
async def register_for_event(
        form: UserBuyTicket,
        service: CreateTicketUseCaseDep,
):
    return await service.do(**form.model_dump())


@router.delete('/{ticket_id}', response_model=CancelTicket)
async def cancel_registration(
        ticket_id: UUID,
        service: CancelTicketUseCaseDep
):
    return await service.do(ticket_id)
