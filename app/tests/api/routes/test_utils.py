from typing import Any

from fastapi.testclient import TestClient

from app.api.deps import get_external_api_service
from app.core.config import settings
from app.main import app
from app.models import ExternalTodo, ExternalTodoPublic


def test_scheduler_status(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    response = client.get(
        f"{settings.API_V1_STR}/utils/scheduler/status/",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    payload = response.json()
    assert "enabled" in payload
    assert "running" in payload
    assert "jobs" in payload


def test_redis_health(client: TestClient, superuser_token_headers: dict[str, str]) -> None:
    response = client.get(
        f"{settings.API_V1_STR}/utils/redis/health/",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    payload = response.json()
    assert "enabled" in payload
    assert "connected" in payload


def test_external_todo_with_dependency_override(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    class FakeExternalApiService:
        async def get_todo(self, *, todo_id: int, refresh: bool = False) -> ExternalTodoPublic:
            return ExternalTodoPublic(
                source="external",
                data=ExternalTodo(
                    userId=1,
                    id=todo_id,
                    title="fake",
                    completed=refresh,
                ),
            )

    app.dependency_overrides[get_external_api_service] = lambda: FakeExternalApiService()
    try:
        response = client.get(
            f"{settings.API_V1_STR}/utils/external/todos/1?refresh=true",
            headers=superuser_token_headers,
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload: dict[str, Any] = response.json()
    assert payload["source"] == "external"
    assert payload["data"]["id"] == 1
    assert payload["data"]["completed"] is True
