import pytest
from httpx import AsyncClient


class TestUsers:
    """用户相关测试"""

    async def get_auth_headers(
        self, client: AsyncClient, test_user_data: dict
    ) -> dict:
        """获取认证头"""
        # 注册并登录用户
        await client.post("/api/v1/auth/register", json=test_user_data)
        response = await client.post(
            "/api/v1/auth/login",
            data={
                "username": test_user_data["email"],
                "password": test_user_data["password"]
            }
        )
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    async def test_get_current_user(
        self, client: AsyncClient, test_user_data: dict
    ):
        """测试获取当前用户信息"""
        headers = await self.get_auth_headers(client, test_user_data)

        response = await client.get("/api/v1/users/me", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_user_data["email"]
        assert data["username"] == test_user_data["username"]
        assert "id" in data
        assert "hashed_password" not in data

    async def test_update_current_user(
        self, client: AsyncClient, test_user_data: dict
    ):
        """测试更新当前用户信息"""
        headers = await self.get_auth_headers(client, test_user_data)

        update_data = {
            "username": "updateduser",
            "email": "updated@example.com"
        }

        response = await client.put(
            "/api/v1/users/me",
            json=update_data,
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == update_data["username"]
        assert data["email"] == update_data["email"]

    async def test_update_user_password(
        self, client: AsyncClient, test_user_data: dict
    ):
        """测试更新用户密码"""
        headers = await self.get_auth_headers(client, test_user_data)

        # 更新密码
        update_data = {
            "password": "newpassword123"
        }

        response = await client.put(
            "/api/v1/users/me",
            json=update_data,
            headers=headers
        )
        assert response.status_code == 200

        # 使用新密码登录
        response = await client.post(
            "/api/v1/auth/login",
            data={
                "username": test_user_data["email"],
                "password": "newpassword123"
            }
        )
        assert response.status_code == 200
        assert "access_token" in response.json()

    async def test_update_user_with_duplicate_email(
        self, client: AsyncClient, test_user_data: dict
    ):
        """测试更新用户为重复邮箱"""
        # 创建两个用户
        user1_data = test_user_data.copy()
        user2_data = {
            "email": "user2@example.com",
            "username": "user2",
            "password": "password123",
            "is_active": True
        }

        await client.post("/api/v1/auth/register", json=user1_data)
        headers = await self.get_auth_headers(client, user2_data)

        # 尝试更新为已存在的邮箱
        update_data = {
            "email": user1_data["email"]
        }

        response = await client.put(
            "/api/v1/users/me",
            json=update_data,
            headers=headers
        )
        assert response.status_code == 400
        assert "Email already registered" in response.json()["detail"]

    async def test_get_user_by_id(
        self, client: AsyncClient, test_user_data: dict
    ):
        """测试通过ID获取用户"""
        headers = await self.get_auth_headers(client, test_user_data)

        # 先获取当前用户信息以获取用户ID
        me_response = await client.get("/api/v1/users/me", headers=headers)
        user_id = me_response.json()["id"]

        # 获取用户信息
        response = await client.get(f"/api/v1/users/{user_id}", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == user_id
        assert data["email"] == test_user_data["email"]

    async def test_get_other_user_forbidden(
        self, client: AsyncClient, test_user_data: dict
    ):
        """测试获取其他用户信息（应被禁止）"""
        headers = await self.get_auth_headers(client, test_user_data)

        # 尝试获取其他用户的信息
        response = await client.get("/api/v1/users/999", headers=headers)
        assert response.status_code == 404

    async def test_get_user_list(
        self, client: AsyncClient, test_user_data: dict
    ):
        """测试获取用户列表"""
        headers = await self.get_auth_headers(client, test_user_data)

        response = await client.get("/api/v1/users/", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # 简化实现，只返回当前用户
        assert len(data) == 1
        assert data[0]["email"] == test_user_data["email"]