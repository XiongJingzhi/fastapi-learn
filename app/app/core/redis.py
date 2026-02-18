import json
import logging
from functools import lru_cache
from typing import Any

from redis.asyncio import Redis
from redis.exceptions import RedisError

from app.core.config import settings

logger = logging.getLogger(__name__)


class RedisCache:
    def __init__(self, client: Redis) -> None:
        self._client = client

    async def get_json(self, key: str) -> dict[str, Any] | None:
        try:
            value = await self._client.get(key)
        except RedisError:
            logger.exception("Redis get failed: key=%s", key)
            return None
        if value is None:
            return None
        if not isinstance(value, str):
            return None
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return None
        return parsed if isinstance(parsed, dict) else None

    async def set_json(self, key: str, value: dict[str, Any], ttl_seconds: int) -> bool:
        try:
            payload = json.dumps(value)
            await self._client.set(key, payload, ex=ttl_seconds)
            return True
        except (TypeError, RedisError):
            logger.exception("Redis set failed: key=%s", key)
            return False

    async def delete(self, key: str) -> bool:
        try:
            await self._client.delete(key)
            return True
        except RedisError:
            logger.exception("Redis delete failed: key=%s", key)
            return False

    async def ping(self) -> bool:
        try:
            return bool(await self._client.ping())
        except RedisError:
            logger.exception("Redis ping failed")
            return False

    async def close(self) -> None:
        try:
            await self._client.aclose()
        except RedisError:
            logger.exception("Redis close failed")


@lru_cache(maxsize=1)
def get_redis_cache() -> RedisCache | None:
    if not settings.REDIS_ENABLED:
        return None
    client = Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        db=settings.REDIS_DB,
        password=settings.REDIS_PASSWORD,
        decode_responses=settings.REDIS_DECODE_RESPONSES,
    )
    return RedisCache(client)


async def close_redis_cache() -> None:
    cache = get_redis_cache()
    if cache:
        await cache.close()
