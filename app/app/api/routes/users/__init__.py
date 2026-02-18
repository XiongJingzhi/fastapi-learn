from fastapi import APIRouter

from app.api.routes.users import commands, queries

router = APIRouter(prefix="/users", tags=["users"])
router.include_router(queries.router)
router.include_router(commands.router)
