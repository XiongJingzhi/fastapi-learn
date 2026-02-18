from contextlib import asynccontextmanager

import sentry_sdk
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute
from starlette.middleware.cors import CORSMiddleware

from app.api.main import api_router
from app.core.config import settings
from app.core.exceptions import AppException
from app.core.redis import close_redis_cache, get_redis_cache
from app.core.scheduler import (
    setup_scheduler_jobs,
    start_scheduler,
    stop_scheduler,
)
from app.integrations.external_api import (
    close_external_todo_client,
    get_external_todo_client,
)
from app.services.external_api import ExternalApiService


def custom_generate_unique_id(route: APIRoute) -> str:
    return f"{route.tags[0]}-{route.name}"


if settings.SENTRY_DSN and settings.ENVIRONMENT != "local":
    sentry_sdk.init(dsn=str(settings.SENTRY_DSN), enable_tracing=True)


async def _scheduled_warmup() -> None:
    service = ExternalApiService(
        external_client=get_external_todo_client(),
        cache=get_redis_cache(),
    )
    await service.warmup_default_todo()


@asynccontextmanager
async def lifespan(_: FastAPI):
    setup_scheduler_jobs(_scheduled_warmup)
    start_scheduler()
    yield
    stop_scheduler()
    await close_external_todo_client()
    await close_redis_cache()


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    generate_unique_id_function=custom_generate_unique_id,
    lifespan=lifespan,
)


@app.exception_handler(AppException)
async def app_exception_handler(_, exc: AppException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )

# Set all CORS enabled origins
if settings.all_cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.all_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(api_router, prefix=settings.API_V1_STR)
