from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.conf import settings
from app.api.routers import main_router

app = FastAPI(
    title=settings.app_title,
    description=settings.app_description
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(main_router)
