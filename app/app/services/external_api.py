from datetime import datetime, timezone

from pydantic import ValidationError

from app.core.config import settings
from app.core.redis import RedisCache
from app.integrations.external_api import ExternalTodoClient
from app.models import ExternalTodo, ExternalTodoPublic


class ExternalApiService:
    def __init__(
        self, *, external_client: ExternalTodoClient, cache: RedisCache | None
    ) -> None:
        self.external_client = external_client
        self.cache = cache

    async def get_todo(self, *, todo_id: int, refresh: bool = False) -> ExternalTodoPublic:
        cache_key = f"external:todo:{todo_id}"
        if not refresh and self.cache:
            cached = await self.cache.get_json(cache_key)
            if cached:
                try:
                    todo = ExternalTodo.model_validate(cached)
                except ValidationError:
                    await self.cache.delete(cache_key)
                else:
                    return ExternalTodoPublic(
                        source="cache",
                        cached_at=datetime.now(timezone.utc),
                        data=todo,
                    )

        payload = await self.external_client.fetch_todo(todo_id)
        todo = ExternalTodo.model_validate(payload)
        if self.cache:
            await self.cache.set_json(
                cache_key,
                todo.model_dump(),
                ttl_seconds=settings.EXTERNAL_API_CACHE_TTL_SECONDS,
            )
        return ExternalTodoPublic(source="external", data=todo)

    async def warmup_default_todo(self) -> ExternalTodoPublic:
        return await self.get_todo(todo_id=settings.EXTERNAL_API_WARMUP_TODO_ID)
