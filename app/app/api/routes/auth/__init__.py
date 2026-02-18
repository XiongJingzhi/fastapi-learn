from fastapi import APIRouter

from app.api.routes.auth import commands, queries

router = APIRouter(tags=["login"])
router.include_router(commands.router)
router.include_router(queries.router)
