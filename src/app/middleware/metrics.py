from starlette.middleware.base import (
    BaseHTTPMiddleware,
    RequestResponseEndpoint,
)
from starlette.requests import Request
from starlette.responses import Response

from app.metrics import http_request_duration_seconds, http_requests_total


class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:

        route = request.scope.get('route')
        if route is not None and hasattr(route, 'path'):
            endpoint = route.path
        else:
            endpoint = request.url.path

        with http_request_duration_seconds.labels(
            method=request.method, endpoint=endpoint
        ).time():
            response = await call_next(request)

        http_requests_total.labels(
            method=request.method,
            endpoint=endpoint,
            status=response.status_code,
        ).inc()

        return response
