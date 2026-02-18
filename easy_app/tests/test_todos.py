import pytest
from httpx import AsyncClient


class TestTodos:
    """待办事项相关测试"""

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

    async def test_create_todo(
        self, client: AsyncClient, test_user_data: dict, test_todo_data: dict
    ):
        """测试创建待办事项"""
        headers = await self.get_auth_headers(client, test_user_data)

        response = await client.post(
            "/api/v1/todos/",
            json=test_todo_data,
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == test_todo_data["title"]
        assert data["description"] == test_todo_data["description"]
        assert data["is_completed"] == test_todo_data["is_completed"]
        assert "id" in data
        assert "owner_id" in data

    async def test_get_todos(
        self, client: AsyncClient, test_user_data: dict, test_todo_data: dict
    ):
        """测试获取待办事项列表"""
        headers = await self.get_auth_headers(client, test_user_data)

        # 创建多个待办事项
        for i in range(3):
            todo_data = test_todo_data.copy()
            todo_data["title"] = f"Todo {i+1}"
            await client.post("/api/v1/todos/", json=todo_data, headers=headers)

        # 获取列表
        response = await client.get("/api/v1/todos/", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 3

    async def test_get_todos_with_pagination(
        self, client: AsyncClient, test_user_data: dict, test_todo_data: dict
    ):
        """测试分页获取待办事项"""
        headers = await self.get_auth_headers(client, test_user_data)

        # 创建多个待办事项
        for i in range(5):
            todo_data = test_todo_data.copy()
            todo_data["title"] = f"Todo {i+1}"
            await client.post("/api/v1/todos/", json=todo_data, headers=headers)

        # 获取分页列表
        response = await client.get("/api/v1/todos/?skip=2&limit=2", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 2

    async def test_get_completed_todos(
        self, client: AsyncClient, test_user_data: dict, test_todo_data: dict
    ):
        """测试获取已完成的待办事项"""
        headers = await self.get_auth_headers(client, test_user_data)

        # 创建不同状态的待办事项
        todo1 = test_todo_data.copy()
        todo1["title"] = "Completed Todo"
        todo1["is_completed"] = True
        await client.post("/api/v1/todos/", json=todo1, headers=headers)

        todo2 = test_todo_data.copy()
        todo2["title"] = "Pending Todo"
        todo2["is_completed"] = False
        await client.post("/api/v1/todos/", json=todo2, headers=headers)

        # 获取已完成的待办事项
        response = await client.get("/api/v1/todos/?completed=true", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["title"] == "Completed Todo"

    async def test_get_todo_stats(
        self, client: AsyncClient, test_user_data: dict, test_todo_data: dict
    ):
        """测试获取待办事项统计"""
        headers = await self.get_auth_headers(client, test_user_data)

        # 创建不同状态的待办事项
        for i in range(2):
            todo_data = test_todo_data.copy()
            todo_data["title"] = f"Completed Todo {i+1}"
            todo_data["is_completed"] = True
            await client.post("/api/v1/todos/", json=todo_data, headers=headers)

        for i in range(3):
            todo_data = test_todo_data.copy()
            todo_data["title"] = f"Pending Todo {i+1}"
            todo_data["is_completed"] = False
            await client.post("/api/v1/todos/", json=todo_data, headers=headers)

        # 获取统计信息
        response = await client.get("/api/v1/todos/stats", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["completed"] == 2
        assert data["pending"] == 3
        assert data["total"] == 5

    async def test_get_todo_by_id(
        self, client: AsyncClient, test_user_data: dict, test_todo_data: dict
    ):
        """测试通过ID获取待办事项"""
        headers = await self.get_auth_headers(client, test_user_data)

        # 创建待办事项
        create_response = await client.post(
            "/api/v1/todos/",
            json=test_todo_data,
            headers=headers
        )
        todo_id = create_response.json()["id"]

        # 获取待办事项
        response = await client.get(f"/api/v1/todos/{todo_id}", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == todo_id
        assert data["title"] == test_todo_data["title"]

    async def test_update_todo(
        self, client: AsyncClient, test_user_data: dict, test_todo_data: dict
    ):
        """测试更新待办事项"""
        headers = await self.get_auth_headers(client, test_user_data)

        # 创建待办事项
        create_response = await client.post(
            "/api/v1/todos/",
            json=test_todo_data,
            headers=headers
        )
        todo_id = create_response.json()["id"]

        # 更新待办事项
        update_data = {
            "title": "Updated Todo",
            "description": "Updated description",
            "is_completed": True
        }
        response = await client.put(
            f"/api/v1/todos/{todo_id}",
            json=update_data,
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == update_data["title"]
        assert data["description"] == update_data["description"]
        assert data["is_completed"] == update_data["is_completed"]

    async def test_mark_todo_completed(
        self, client: AsyncClient, test_user_data: dict, test_todo_data: dict
    ):
        """测试标记待办事项为已完成"""
        headers = await self.get_auth_headers(client, test_user_data)

        # 创建未完成的待办事项
        todo_data = test_todo_data.copy()
        todo_data["is_completed"] = False
        create_response = await client.post(
            "/api/v1/todos/",
            json=todo_data,
            headers=headers
        )
        todo_id = create_response.json()["id"]

        # 标记为已完成
        response = await client.patch(
            f"/api/v1/todos/{todo_id}/complete",
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_completed"] is True

    async def test_delete_todo(
        self, client: AsyncClient, test_user_data: dict, test_todo_data: dict
    ):
        """测试删除待办事项"""
        headers = await self.get_auth_headers(client, test_user_data)

        # 创建待办事项
        create_response = await client.post(
            "/api/v1/todos/",
            json=test_todo_data,
            headers=headers
        )
        todo_id = create_response.json()["id"]

        # 删除待办事项
        response = await client.delete(
            f"/api/v1/todos/{todo_id}",
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == todo_id

        # 确认待办事项已被删除
        response = await client.get(f"/api/v1/todos/{todo_id}", headers=headers)
        assert response.status_code == 404

    async def test_unauthorized_todo_access(
        self, client: AsyncClient, test_user_data: dict, test_todo_data: dict
    ):
        """测试未授权访问待办事项"""
        headers = await self.get_auth_headers(client, test_user_data)

        # 尝试访问不存在的待办事项
        response = await client.get("/api/v1/todos/999", headers=headers)
        assert response.status_code == 404

    async def test_create_todo_without_auth(
        self, client: AsyncClient, test_todo_data: dict
    ):
        """测试未认证时创建待办事项"""
        response = await client.post("/api/v1/todos/", json=test_todo_data)
        assert response.status_code == 401