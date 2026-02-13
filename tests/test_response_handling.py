import importlib

import pytest
from fastapi.testclient import TestClient


response_handling = importlib.import_module("app.examples.02_response_handling")
app = response_handling.app


@pytest.fixture(autouse=True)
def reset_demo_state():
    response_handling.fake_db.clear()
    response_handling.user_id_counter = 1


@pytest.fixture
def client():
    return TestClient(app)


def test_user_endpoints(client: TestClient):
    create_resp = client.post(
        "/api/users/",
        json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "password123",
        },
    )
    assert create_resp.status_code == 201
    created_user = create_resp.json()
    assert created_user["id"] == 1
    assert created_user["username"] == "testuser"
    assert created_user["email"] == "test@example.com"
    assert "hashed_password" not in created_user

    get_resp = client.get(f"/api/users/{created_user['id']}")
    assert get_resp.status_code == 200
    fetched_user = get_resp.json()
    assert fetched_user["id"] == created_user["id"]
    assert "hashed_password" not in fetched_user

    list_resp = client.get("/api/users/")
    assert list_resp.status_code == 200
    users = list_resp.json()
    assert len(users) == 1
    assert users[0]["username"] == "testuser"


def test_status_codes_and_custom_error(client: TestClient):
    assert client.get("/api/status/ok").status_code == 200
    assert client.post("/api/status/created").status_code == 201

    not_found_resp = client.get("/api/error/not-found")
    assert not_found_resp.status_code == 404
    assert not_found_resp.json()["detail"] == "请求的资源不存在"

    custom_error_resp = client.get("/api/error/custom")
    assert custom_error_resp.status_code == 400
    assert custom_error_resp.json()["error"] is True


def test_headers(client: TestClient):
    custom_resp = client.get("/api/headers/custom")
    assert custom_resp.status_code == 200
    assert custom_resp.headers["X-Custom-Header"] == "Custom Value"
    assert custom_resp.headers["X-Request-ID"] == "req-12345"

    cors_resp = client.get("/api/headers/cors")
    assert cors_resp.status_code == 200
    assert cors_resp.headers["Access-Control-Allow-Origin"] == "*"


def test_streaming_response(client: TestClient):
    with client.stream("GET", "/api/stream/data") as resp:
        assert resp.status_code == 200
        first_line = next(line for line in resp.iter_lines() if line)
    assert first_line.startswith("数据行 0")


def test_redirect(client: TestClient):
    redirect_resp = client.get("/api/redirect/old-url", follow_redirects=False)
    assert redirect_resp.status_code == 307
    assert redirect_resp.headers["location"] == "/api/headers/basic"
