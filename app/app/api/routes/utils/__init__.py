from fastapi import APIRouter

from app.api.routes.utils import commands, queries

router = APIRouter(prefix="/utils", tags=["utils"])
router.include_router(queries.router)
router.include_router(commands.router)
