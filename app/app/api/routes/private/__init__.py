from fastapi import APIRouter

from app.api.routes.private import commands, queries

router = APIRouter(tags=["private"], prefix="/private")
router.include_router(queries.router)
router.include_router(commands.router)
