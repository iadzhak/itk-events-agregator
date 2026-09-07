from uuid import UUID

from cachetools import TTLCache

from app.clients import BaseProviderClient
from app.schemas import EventSeatsResponse

CACHE_MAX_SIZE = 30
CACHE_TTL = 30

seats_cache = TTLCache(maxsize=CACHE_MAX_SIZE, ttl=CACHE_TTL)


def get_seats_cache():
    return seats_cache


class AvailableSeatsUseCase:
    def __init__(self, client: BaseProviderClient, cache: TTLCache) -> None:
        self._client = client
        self._cache = cache

    async def _get_available_seats(self, event_id: UUID) -> tuple[str]:
        if event_id not in self._cache:
            result = await self._client.seats(event_id)
            self._cache[event_id] = tuple(result)
        return self._cache[event_id]

    async def do(self, event_id: UUID) -> EventSeatsResponse:
        seats = await self._get_available_seats(event_id)
        return EventSeatsResponse(
            event_id=event_id,
            available_seats=list(seats)
        )
