"""
Level 1 - Example 03: 统一响应格式 (Unified Response Format)

本示例展示如何设计和使用统一的 API 响应格式：
1. 定义统一的响应模型 (ApiResponse)
2. 分页响应格式 (PaginatedResponse)
3. 响应辅助函数 (success_response, paginated_response)
4. 在 Endpoint 中使用统一格式

运行方式:
    uvicorn study.level1.examples.03_unified_response:app --reload
"""

from fastapi import FastAPI, Query, status
from pydantic import BaseModel, Field, ConfigDict
from typing import Generic, TypeVar, Optional, List
import time

app = FastAPI(title="Level 1 - Unified Response Format")


# ========== 统一响应模型 ==========

T = TypeVar('T')


class ApiResponse(BaseModel, Generic[T]):
    """
    统一响应格式

    所有 API 接口都返回这个格式，确保：
    - 前端可以统一处理响应
    - 包含时间戳便于调试
    - 便于添加全局功能（如国际化）
    """
    code: int = Field(200, description="业务状态码")
    message: str = Field("success", description="响应消息")
    data: Optional[T] = Field(None, description="响应数据")
    timestamp: int = Field(default_factory=lambda: int(time.time()), description="时间戳")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "code": 200,
                "message": "操作成功",
                "data": {"id": 1},
                "timestamp": 1736784000
            }
        }
    )


class PaginationMeta(BaseModel):
    """分页元数据"""
    total: int = Field(..., description="总记录数")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页大小")
    pages: int = Field(..., description="总页数")


class PaginatedData(BaseModel, Generic[T]):
    """分页数据"""
    items: List[T] = Field(..., description="数据列表")
    pagination: PaginationMeta = Field(..., description="分页信息")


# ========== 数据模型 ==========

class UserResponse(BaseModel):
    """用户响应模型"""
    id: int
    username: str
    email: str
    full_name: Optional[str] = None


class ItemResponse(BaseModel):
    """商品响应模型"""
    id: int
    name: str
    price: float
    in_stock: bool


# ========== 响应辅助函数 ==========

def success_response(
    data: any = None,
    message: str = "操作成功",
    code: int = 200
) -> dict:
    """
    创建成功响应

    Args:
        data: 响应数据
        message: 响应消息
        code: 业务状态码

    Returns:
        统一格式的响应字典
    """
    return {
        "code": code,
        "message": message,
        "data": data,
        "timestamp": int(time.time())
    }


def error_response(
    message: str = "操作失败",
    code: int = 400,
    data: any = None
) -> dict:
    """
    创建错误响应

    Args:
        message: 错误消息
        code: 业务状态码
        data: 错误详情

    Returns:
        统一格式的错误响应字典
    """
    return {
        "code": code,
        "message": message,
        "data": data,
        "timestamp": int(time.time())
    }


def paginated_response(
    items: list[any],
    total: int,
    page: int,
    page_size: int,
    message: str = "查询成功"
) -> dict:
    """
    创建分页响应

    Args:
        items: 数据列表
        total: 总记录数
        page: 当前页码
        page_size: 每页大小
        message: 响应消息

    Returns:
        包含分页信息的统格式响应
    """
    pages = (total + page_size - 1) // page_size  # 计算总页数

    paginated_data = {
        "items": items,
        "pagination": {
            "total": total,
            "page": page,
            "page_size": page_size,
            "pages": pages
        }
    }

    return success_response(data=paginated_data, message=message)


# ========== 模拟数据库 ==========

fake_users = [
    {"id": i, "username": f"user{i}", "email": f"user{i}@example.com"}
    for i in range(1, 101)
]

fake_items = [
    {"id": i, "name": f"Item {i}", "price": i * 10.0, "in_stock": i % 2 == 0}
    for i in range(1, 51)
]


# ========== API 端点 ==========

@app.get("/", response_model=ApiResponse[dict])
async def root():
    """根端点 - API 信息"""
    return success_response(
        data={
            "name": "Unified Response Format Demo",
            "version": "1.0.0",
            "endpoints": {
                "users": "/users",
                "items": "/items",
                "users_paginated": "/users/paginated"
            }
        },
        message="API 信息"
    )


# ========== 示例 1：单个资源响应 ==========

@app.get("/users/{user_id}", response_model=ApiResponse[UserResponse])
async def get_user(user_id: int):
    """
    获取单个用户

    响应格式：
    {
        "code": 200,
        "message": "查询成功",
        "data": {"id": 1, "username": "user1", "email": "user1@example.com"},
        "timestamp": 1736784000
    }
    """
    # 模拟数据库查询
    user = next((u for u in fake_users if u["id"] == user_id), None)

    if not user:
        return error_response(
            message=f"用户 {user_id} 不存在",
            code=404
        )

    return success_response(
        data=user,
        message="查询成功"
    )


# ========== 示例 2：列表响应（带分页）==========

@app.get("/users", response_model=ApiResponse[dict])
async def list_users(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页大小")
):
    """
    获取用户列表（分页）

    响应格式：
    {
        "code": 200,
        "message": "查询成功",
        "data": {
            "items": [...],
            "pagination": {
                "total": 100,
                "page": 1,
                "page_size": 10,
                "pages": 10
            }
        },
        "timestamp": 1736784000
    }
    """
    # 计算分页
    start = (page - 1) * page_size
    end = start + page_size

    paginated_users = fake_users[start:end]

    return paginated_response(
        items=paginated_users,
        total=len(fake_users),
        page=page,
        page_size=page_size
    )


@app.get("/items", response_model=ApiResponse[dict])
async def list_items(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50)
):
    """获取商品列表（分页）"""
    start = (page - 1) * page_size
    end = start + page_size

    paginated_items = fake_items[start:end]

    return paginated_response(
        items=paginated_items,
        total=len(fake_items),
        page=page,
        page_size=page_size
    )


# ========== 示例 3：创建资源 ==========

@app.post("/users", response_model=ApiResponse[UserResponse], status_code=201)
async def create_user(user_data: dict):
    """
    创建用户

    响应格式：
    {
        "code": 201,
        "message": "创建成功",
        "data": {"id": 101, "username": "newuser", ...},
        "timestamp": 1736784000
    }
    """
    # 模拟创建用户
    new_user = {
        "id": len(fake_users) + 1,
        "username": user_data.get("username", "newuser"),
        "email": user_data.get("email", "newuser@example.com")
    }

    fake_users.append(new_user)

    return success_response(
        data=new_user,
        message="创建成功",
        code=201
    )


# ========== 示例 4：无数据响应 ==========

@app.delete("/users/{user_id}", response_model=ApiResponse[dict])
async def delete_user(user_id: int):
    """
    删除用户（成功时不返回数据）

    响应格式：
    {
        "code": 200,
        "message": "删除成功",
        "data": null,
        "timestamp": 1736784000
    }
    """
    user = next((u for u in fake_users if u["id"] == user_id), None)

    if not user:
        return error_response(
            message=f"用户 {user_id} 不存在",
            code=404
        )

    # 模拟删除
    if user in fake_users:
        fake_users.remove(user)

    return success_response(
        data=None,
        message="删除成功"
    )


# ========== 示例 5：搜索和筛选 ==========

@app.get("/users/search", response_model=ApiResponse[dict])
async def search_users(
    q: str = Query(..., min_length=1, description="搜索关键词"),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50)
):
    """
    搜索用户（支持分页）

    响应格式：
    {
        "code": 200,
        "message": "搜索完成",
        "data": {
            "items": [...],
            "pagination": {...}
        },
        "timestamp": 1736784000
    }
    """
    # 筛选匹配的用户
    filtered_users = [
        u for u in fake_users
        if q.lower() in u["username"].lower() or q in u["email"]
    ]

    # 分页
    start = (page - 1) * page_size
    end = start + page_size
    paginated_users = filtered_users[start:end]

    return paginated_response(
        items=paginated_users,
        total=len(filtered_users),
        page=page,
        page_size=page_size,
        message="搜索完成"
    )


# ========== 示例 6：错误响应 ==========

@app.get("/users/{user_id}/error", response_model=ApiResponse[dict])
async def get_user_with_error_handling(user_id: int):
    """
    错误响应示例

    错误响应格式：
    {
        "code": 404,
        "message": "用户不存在",
        "data": null,
        "timestamp": 1736784000
    }
    """
    user = next((u for u in fake_users if u["id"] == user_id), None)

    if not user:
        return error_response(
            message=f"用户 {user_id} 不存在",
            code=404
        )

    return success_response(
        data=user,
        message="查询成功"
    )


# ========== 主程序入口 ==========

if __name__ == "__main__":
    import uvicorn

    print("=" * 60)
    print("FastAPI Unified Response Format Demo")
    print("=" * 60)
    print()
    print("测试端点：")
    print("  单个资源：")
    print("    curl http://localhost:8000/users/1")
    print()
    print("  列表（分页）：")
    print("    curl 'http://localhost:8000/users?page=1&page_size=5'")
    print()
    print("  创建资源：")
    print("    curl -X POST http://localhost:8000/users \\")
    print("      -H 'Content-Type: application/json' \\")
    print("      -d '{\"username\": \"test\", \"email\": \"test@example.com\"}'")
    print()
    print("  搜索：")
    print("    curl 'http://localhost:8000/users/search?q=user1&page=1'")
    print()
    print("  错误响应：")
    print("    curl http://localhost:8000/users/999/error")
    print()
    print("=" * 60)

    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
