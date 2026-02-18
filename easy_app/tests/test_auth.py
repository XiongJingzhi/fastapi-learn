import pytest
from httpx import AsyncClient


class TestAuth:
    """认证相关测试"""

    async def test_register_user(
        self, client: AsyncClient, test_user_data: dict
    ):
        """测试用户注册"""
        response = await client.post(
            "/api/v1/auth/register",
            json=test_user_data
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_user_data["email"]
        assert data["username"] == test_user_data["username"]
        assert "id" in data
        assert "hashed_password" not in data

    async def test_register_duplicate_email(
        self, client: AsyncClient, test_user_data: dict
    ):
        """测试重复邮箱注册"""
        # 先注册一个用户
        await client.post("/api/v1/auth/register", json=test_user_data)

        # 再次使用相同邮箱注册
        response = await client.post(
            "/api/v1/auth/register",
            json=test_user_data
        )
        assert response.status_code == 400
        assert "Email already registered" in response.json()["detail"]

    async def test_register_duplicate_username(
        self, client: AsyncClient, test_user_data: dict
    ):
        """测试重复用户名注册"""
        # 先注册一个用户
        await client.post("/api/v1/auth/register", json=test_user_data)

        # 使用相同用户名注册
        duplicate_user = test_user_data.copy()
        duplicate_user["email"] = "another@example.com"
        response = await client.post(
            "/api/v1/auth/register",
            json=duplicate_user
        )
        assert response.status_code == 400
        assert "Username already taken" in response.json()["detail"]

    async def test_login_success(
        self, client: AsyncClient, test_user_data: dict
    ):
        """测试成功登录"""
        # 先注册用户
        await client.post("/api/v1/auth/register", json=test_user_data)

        # 登录
        response = await client.post(
            "/api/v1/auth/login",
            data={
                "username": test_user_data["email"],
                "password": test_user_data["password"]
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    async def test_login_json_success(
        self, client: AsyncClient, test_user_data: dict
    ):
        """测试JSON格式登录"""
        # 先注册用户
        await client.post("/api/v1/auth/register", json=test_user_data)

        # 登录
        response = await client.post(
            "/api/v1/auth/login-json",
            json={
                "email": test_user_data["email"],
                "password": test_user_data["password"]
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    async def test_login_invalid_email(
        self, client: AsyncClient, test_user_data: dict
    ):
        """测试无效邮箱登录"""
        response = await client.post(
            "/api/v1/auth/login",
            data={
                "username": "wrong@example.com",
                "password": test_user_data["password"]
            }
        )
        assert response.status_code == 401
        assert "Incorrect email or password" in response.json()["detail"]

    async def test_login_invalid_password(
        self, client: AsyncClient, test_user_data: dict
    ):
        """测试无效密码登录"""
        # 先注册用户
        await client.post("/api/v1/auth/register", json=test_user_data)

        # 使用错误密码登录
        response = await client.post(
            "/api/v1/auth/login",
            data={
                "username": test_user_data["email"],
                "password": "wrongpassword"
            }
        )
        assert response.status_code == 401
        assert "Incorrect email or password" in response.json()["detail"]

    async def test_access_protected_route_without_token(self, client: AsyncClient):
        """测试未授权访问受保护路由"""
        response = await client.get("/api/v1/users/me")
        assert response.status_code == 401

    async def test_access_protected_route_with_invalid_token(self, client: AsyncClient):
        """测试使用无效令牌访问受保护路由"""
        headers = {"Authorization": "Bearer invalid_token"}
        response = await client.get("/api/v1/users/me", headers=headers)
        assert response.status_code == 401