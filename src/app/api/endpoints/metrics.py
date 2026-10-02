import asyncio

from fastapi import APIRouter, Response
from prometheus_client import REGISTRY, generate_latest

from app.dependencies import EventsRepoDep, TicketRepoDep
from app.metrics import (
    events_total,
    tickets_cancelled_total,
    tickets_created_total,
)
from app.types import TicketStatus

router = APIRouter()


@router.get('/metrics')
async def metrics(tickets: TicketRepoDep, events: EventsRepoDep):
    t_t, t_c, e_t = await asyncio.gather(
        tickets.count(),
        tickets.count_by_status(TicketStatus.CANCELLED),
        events.count(),
    )
    tickets_created_total.set(t_t)
    tickets_cancelled_total.set(t_c)
    events_total.set(e_t)
    return Response(content=generate_latest(REGISTRY), media_type='text/plain')
