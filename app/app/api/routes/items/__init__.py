from fastapi import APIRouter

from app.api.routes.items import commands, queries

router = APIRouter(prefix="/items", tags=["items"])
router.include_router(queries.router)
router.include_router(commands.router)
