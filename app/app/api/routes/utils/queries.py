from fastapi import APIRouter, Depends

from app.api.deps import ExternalApiServiceDep, get_current_active_superuser
from app.core.config import settings
from app.core.redis import get_redis_cache
from app.core.scheduler import get_scheduler_status
from app.models import ExternalTodoPublic, RedisHealthPublic, SchedulerStatusPublic

router = APIRouter()


@router.get("/health-check/")
async def health_check() -> bool:
    return True


@router.get(
    "/redis/health/",
    response_model=RedisHealthPublic,
    dependencies=[Depends(get_current_active_superuser)],
)
async def redis_health() -> RedisHealthPublic:
    cache = get_redis_cache()
    if not cache:
        return RedisHealthPublic(enabled=False, connected=False)
    return RedisHealthPublic(enabled=True, connected=await cache.ping())


@router.get(
    "/external/todos/{todo_id}",
    response_model=ExternalTodoPublic,
    dependencies=[Depends(get_current_active_superuser)],
)
async def read_external_todo(
    todo_id: int,
    service: ExternalApiServiceDep,
    refresh: bool = False,
) -> ExternalTodoPublic:
    return await service.get_todo(todo_id=todo_id, refresh=refresh)


@router.get(
    "/scheduler/status/",
    response_model=SchedulerStatusPublic,
    dependencies=[Depends(get_current_active_superuser)],
)
async def scheduler_status() -> SchedulerStatusPublic:
    running, jobs = get_scheduler_status()
    return SchedulerStatusPublic(enabled=settings.SCHEDULER_ENABLED, running=running, jobs=jobs)
