import logging
from functools import lru_cache
from typing import Any

import httpx
from tenacity import RetryError, retry, stop_after_attempt, wait_fixed

from app.core.config import settings
from app.core.exceptions import AppException

logger = logging.getLogger(__name__)


class ExternalTodoClient:
    def __init__(self, base_url: str, timeout_seconds: float) -> None:
        self._client = httpx.AsyncClient(
            base_url=base_url,
            timeout=httpx.Timeout(timeout_seconds),
            headers={"Accept": "application/json"},
        )

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(0.2), reraise=True)
    async def fetch_todo(self, todo_id: int) -> dict[str, Any]:
        try:
            response = await self._client.get(f"/todos/{todo_id}")
            response.raise_for_status()
        except httpx.TimeoutException as exc:
            raise AppException(
                status_code=503,
                detail="External API timeout",
                error_code="EXTERNAL_API_TIMEOUT",
            ) from exc
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 404:
                raise AppException(
                    status_code=404,
                    detail="External todo not found",
                    error_code="EXTERNAL_TODO_NOT_FOUND",
                ) from exc
            raise AppException(
                status_code=503,
                detail="External API returned an error",
                error_code="EXTERNAL_API_HTTP_ERROR",
            ) from exc
        except httpx.HTTPError as exc:
            raise AppException(
                status_code=503,
                detail="External API request failed",
                error_code="EXTERNAL_API_REQUEST_ERROR",
            ) from exc

        data = response.json()
        if not isinstance(data, dict):
            raise AppException(
                status_code=502,
                detail="External API returned invalid payload",
                error_code="EXTERNAL_API_PAYLOAD_INVALID",
            )
        return data

    async def close(self) -> None:
        await self._client.aclose()


@lru_cache(maxsize=1)
def get_external_todo_client() -> ExternalTodoClient:
    return ExternalTodoClient(
        base_url=settings.EXTERNAL_API_BASE_URL,
        timeout_seconds=settings.EXTERNAL_API_TIMEOUT_SECONDS,
    )


async def close_external_todo_client() -> None:
    client = get_external_todo_client()
    await client.close()


def is_retryable_external_error(exc: Exception) -> bool:
    if isinstance(exc, AppException):
        return exc.status_code >= 500
    if isinstance(exc, RetryError):
        return True
    logger.exception("Unexpected external API error type")
    return False
