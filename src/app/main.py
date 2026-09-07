from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware

from app.api import main_router
from app.core import EventBaseException, ExternalApiError, settings
from app.lifespan import lifespan

app = FastAPI(
    title=settings.app_title,
    description=settings.app_description,
    lifespan=lifespan
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(main_router)


@app.exception_handler(ExternalApiError)
async def handle_external_api_error(request: Request, exc: ExternalApiError):
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail='Внешний сервис не доступен'
    )


@app.exception_handler(EventBaseException)
async def handle_bad_request_exceptions(
        request: Request,
        exc: EventBaseException
):
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=str(exc)
    )
