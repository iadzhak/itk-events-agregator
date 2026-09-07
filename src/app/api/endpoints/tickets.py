from fastapi import APIRouter

from app.dependencies import CreateTicketUseCaseDep, SessionDep
from app.schemas import UserBuyTicket

router = APIRouter()


@router.post('/')
async def register_for_event(
        form: UserBuyTicket,
        usecase: CreateTicketUseCaseDep,
        session: SessionDep
):
    return await usecase.do(form.event_id, form.first_name, form.seat, session)


@router.delete('/{ticket_id}')
async def cancel_registration():
    return None
