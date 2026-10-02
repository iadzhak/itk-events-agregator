from fastapi import APIRouter, Response
from prometheus_client import REGISTRY, generate_latest

from app.dependencies import EventsRepoDep, TicketRepoDep
from app.metrics import (
    events_total,
    tickets_cancelled_total,
    tickets_created_total,
)

router = APIRouter()


@router.get('/metrics')
async def metrics(tickets: TicketRepoDep, events: EventsRepoDep):
    tickets_created_total.set(await tickets.count())
    tickets_cancelled_total.set(await tickets.count_cancelled())
    events_total.set(await events.count())
    return Response(content=generate_latest(REGISTRY), media_type='text/plain')
