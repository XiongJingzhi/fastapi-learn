from fastapi import APIRouter

from app.api.routes import private, utils
from app.api.routes.auth import router as auth_router
from app.api.routes.items import router as items_router
from app.api.routes.users import router as users_router
from app.core.config import settings

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(utils.router)
api_router.include_router(items_router)


if settings.ENVIRONMENT == "local":
    api_router.include_router(private.router)
