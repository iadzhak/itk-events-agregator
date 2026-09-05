from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routers import main_router
from app.core.conf import settings
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
